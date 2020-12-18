# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
from typing import List, Optional, Dict, Set, Union

import gitlab
from gitlab.v4.objects import GitlabGetError, Project as GitlabObjectsProject

from ogr.abstract import (
    PullRequest,
    Issue,
    Release,
    GitTag,
    IssueStatus,
    CommitFlag,
    PRStatus,
    CommitComment,
    CommitStatus,
    AccessLevel,
)
from ogr.exceptions import GitlabAPIException, OperationNotSupported
from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BaseGitProject
from ogr.services.gitlab.flag import GitlabCommitFlag
from ogr.services.gitlab.issue import GitlabIssue
from ogr.services.gitlab.pull_request import GitlabPullRequest
from ogr.services.gitlab.release import GitlabRelease
from ogr.utils import filter_paths

logger = logging.getLogger(__name__)


class GitlabProject(BaseGitProject):
    service: "ogr_gitlab.GitlabService"

    def __init__(
        self,
        repo: str,
        service: "ogr_gitlab.GitlabService",
        namespace: str,
        gitlab_repo=None,
        **unprocess_kwargs,
    ) -> None:
        if unprocess_kwargs:
            logger.warning(
                f"GitlabProject will not process these kwargs: {unprocess_kwargs}"
            )
        super().__init__(repo, service, namespace)
        self._gitlab_repo = gitlab_repo
        self.read_only = False

    @property
    def gitlab_repo(self) -> GitlabObjectsProject:
        if not self._gitlab_repo:
            self._gitlab_repo = self.service.gitlab_instance.projects.get(
                f"{self.namespace}/{self.repo}"
            )
        return self._gitlab_repo

    @property
    def is_fork(self) -> bool:
        return bool("forked_from_project" in self.gitlab_repo.attributes)

    @property
    def parent(self) -> Optional["GitlabProject"]:
        """
        Return parent project if this project is a fork, otherwise return None
        """
        if self.is_fork:
            parent_dict = self.gitlab_repo.attributes["forked_from_project"]
            return GitlabProject(
                repo=parent_dict["path"],
                service=self.service,
                namespace=parent_dict["namespace"]["full_path"],
            )
        return None

    @property
    def default_branch(self) -> Optional[str]:
        return self.gitlab_repo.attributes.get("default_branch")

    def __str__(self) -> str:
        return f'GitlabProject(namespace="{self.namespace}", repo="{self.repo}")'

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, GitlabProject):
            return False

        return (
            self.repo == o.repo
            and self.namespace == o.namespace
            and self.service == o.service
        )

    def _construct_fork_project(self) -> Optional["GitlabProject"]:
        user_login = self.service.user.get_username()
        try:
            project = GitlabProject(
                repo=self.repo, service=self.service, namespace=user_login
            )
            if project.gitlab_repo:
                return project
        except Exception as ex:
            logger.debug(f"Project {self.repo}/{user_login} does not exist: {ex}")
        return None

    def exists(self) -> bool:
        try:
            _ = self.gitlab_repo
            return True
        except GitlabGetError as ex:
            if "404 Project Not Found" in str(ex):
                return False
            raise GitlabAPIException from ex

    def is_private(self) -> bool:
        """
        Is this repo private? (accessible only by users with granted access)

        :return: if yes, return True
        """
        return self.gitlab_repo.attributes["visibility"] == "private"

    def is_forked(self) -> bool:
        return bool(self._construct_fork_project())

    def get_description(self) -> str:
        return self.gitlab_repo.attributes["description"]

    def get_fork(self, create: bool = True) -> Optional["GitlabProject"]:
        """
        Provide GitlabProject instance of a fork of this project.

        Returns None if this is a fork.

        :param create: create a fork if it doesn't exist
        :return: instance of GitlabProject
        """
        username = self.service.user.get_username()
        for fork in self.get_forks():
            if fork.gitlab_repo.namespace["full_path"] == username:
                return fork

        if not self.is_forked():
            if create:
                return self.fork_create()
            else:
                logger.info(
                    f"Fork of {self.gitlab_repo.attributes['name']}"
                    " does not exist and we were asked not to create it."
                )
                return None
        return self._construct_fork_project()

    def get_owners(self) -> List[str]:
        return self._get_collaborators_with_given_access(
            access_levels=[gitlab.OWNER_ACCESS]
        )

    def who_can_close_issue(self) -> Set[str]:
        return set(
            self._get_collaborators_with_given_access(
                access_levels=[
                    gitlab.REPORTER_ACCESS,
                    gitlab.DEVELOPER_ACCESS,
                    gitlab.MAINTAINER_ACCESS,
                    gitlab.OWNER_ACCESS,
                ]
            )
        )

    def who_can_merge_pr(self) -> Set[str]:
        return set(
            self._get_collaborators_with_given_access(
                access_levels=[
                    gitlab.DEVELOPER_ACCESS,
                    gitlab.MAINTAINER_ACCESS,
                    gitlab.OWNER_ACCESS,
                ]
            )
        )

    def can_merge_pr(self, username) -> bool:
        return username in self.who_can_merge_pr()

    def delete(self) -> None:
        self.gitlab_repo.delete()

    def _get_collaborators_with_given_access(
        self, access_levels: List[int]
    ) -> List[str]:
        """
        Get all project collaborators with one of the given access levels.
        Access levels:
            10 => Guest access
            20 => Reporter access
            30 => Developer access
            40 => Maintainer access
            50 => Owner access
        :return: List of usernames
        """
        response = []
        for member in self.gitlab_repo.members.all(all=True):
            if isinstance(member, dict):
                access_level = member["access_level"]
                username = member["username"]
            else:
                access_level = member.access_level
                username = member.username
            if access_level in access_levels:
                response.append(username)
        return response

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        """
        AccessLevel.pull => Guest access
        AccessLevel.triage => Reporter access
        AccessLevel.push => Developer access
        AccessLevel.admin => Maintainer access
        AccessLevel.maintain => Owner access # Only valid for groups
        """
        access_dict = {
            AccessLevel.pull: gitlab.GUEST_ACCESS,
            AccessLevel.triage: gitlab.REPORTER_ACCESS,
            AccessLevel.push: gitlab.DEVELOPER_ACCESS,
            AccessLevel.admin: gitlab.MAINTAINER_ACCESS,
            AccessLevel.maintain: gitlab.OWNER_ACCESS,
        }
        try:
            user_id = self.service.gitlab_instance.users.list(username=user)[0].id
        except Exception as e:
            raise GitlabAPIException(f"User {user} not found", e)
        try:
            self.gitlab_repo.members.create(
                {"user_id": user_id, "access_level": access_dict[access_level]}
            )
        except Exception as e:
            raise GitlabAPIException(f"User {user} already exists", e)

    def request_access(self) -> None:
        try:
            self.gitlab_repo.accessrequests.create({})
        except gitlab.exceptions.GitlabCreateError as e:
            raise GitlabAPIException("Unable to request access", e)

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List["PullRequest"]:
        return GitlabPullRequest.get_list(project=self, status=status)

    def get_sha_from_tag(self, tag_name: str) -> str:
        try:
            tag = self.gitlab_repo.tags.get(tag_name)
            return tag.attributes["commit"]["id"]
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Tag {tag_name} was not found.")
            raise GitlabAPIException(f"Tag {tag_name} was not found.", ex)

    def create_pr(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        return GitlabPullRequest.create(
            project=self,
            title=title,
            body=body,
            target_branch=target_branch,
            source_branch=source_branch,
            fork_username=fork_username,
        )

    def commit_comment(
        self, commit: str, body: str, filename: str = None, row: int = None
    ) -> "CommitComment":
        """
        Create comment on a commit.

        :param commit: str The SHA of the commit needing a comment.
        :param body: str The text of the comment
        :param filename: str The relative path to the file that necessitates a comment
        :param row: int Line index in the diff to comment on.
        :return: CommitComment
        """
        try:
            commit_object = self.gitlab_repo.commits.get(commit)
        except gitlab.exceptions.GitlabGetError:
            logger.error(f"Commit {commit} was not found.")
            raise GitlabAPIException(f"Commit {commit} was not found.")

        if filename and row:
            raw_comment = commit_object.comments.create(
                {"note": body, "path": filename, "line": row, "line_type": "new"}
            )
        else:
            raw_comment = commit_object.comments.create({"note": body})
        return self._commit_comment_from_gitlab_object(raw_comment, commit)

    def set_commit_status(
        self,
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "CommitFlag":
        """
        Create a status on a commit

        :param commit: The SHA of the commit.
        :param state: The state of the status.
        :param target_url: The target URL to associate with this status.
        :param description: A short description of the status
        :param context: A label to differentiate this status from the status of other systems.
        :param trim: Whether to trim the description to 140 characters
        :return: CommitFlag
        """
        return GitlabCommitFlag.set(
            project=self,
            commit=commit,
            state=state,
            target_url=target_url,
            description=description,
            context=context,
            trim=trim,
        )

    def get_commit_statuses(self, commit: str) -> List[CommitFlag]:
        """
        Get the statuses of a commit in a project.
        :param commit: The SHA of the commit.
        :return: [CommitFlag]
        """
        return GitlabCommitFlag.get(project=self, commit=commit)

    def get_git_urls(self) -> Dict[str, str]:
        return {
            "git": self.gitlab_repo.attributes["http_url_to_repo"],
            "ssh": self.gitlab_repo.attributes["ssh_url_to_repo"],
        }

    def fork_create(self) -> "GitlabProject":
        """
        Fork this project using the authenticated user.
        This may raise an exception if the fork already exists.

        :return: fork GitlabProject instance
        """
        try:
            fork = self.gitlab_repo.forks.create({})
        except gitlab.GitlabCreateError:
            logger.error(f"Repo {self.gitlab_repo} cannot be forked")
            raise GitlabAPIException(f"Repo {self.gitlab_repo} cannot be forked")
        return GitlabProject(
            namespace=fork.namespace["full_path"], service=self.service, repo=fork.path
        )

    def change_token(self, new_token: str):
        self.service.change_token(new_token)

    def get_branches(self) -> List[str]:
        return [branch.name for branch in self.gitlab_repo.branches.list(all=True)]

    def get_file_content(self, path, ref=None) -> str:
        ref = ref or self.default_branch
        try:
            file = self.gitlab_repo.files.get(file_path=path, ref=ref)
            return file.decode().decode()
        except gitlab.exceptions.GitlabGetError as ex:
            raise FileNotFoundError(f"File '{path}' on {ref} not found", ex)

    def get_files(
        self, ref: str = None, filter_regex: str = None, recursive: bool = False
    ) -> List[str]:
        """
        Get a list of file paths of the repo.
        :param ref: branch or commit (defaults to repo's default branch)
        :param filter_regex: filter the paths with re.search
        :param recursive: whether to return only top directory files or all files recursively
        :return: [str]
        """
        ref = ref or self.default_branch
        paths = [
            file_dict["path"]
            for file_dict in self.gitlab_repo.repository_tree(
                ref=ref, recursive=recursive, all=True
            )
            if file_dict["type"] != "tree"
        ]
        if filter_regex:
            paths = filter_paths(paths, filter_regex)

        return paths

    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List[Issue]:
        return GitlabIssue.get_list(
            project=self, status=status, author=author, assignee=assignee, labels=labels
        )

    def get_issue(self, issue_id: int) -> Issue:
        return GitlabIssue.get(project=self, id=issue_id)

    def create_issue(
        self,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Issue:

        ids = []
        for user in assignees or []:
            users_list = self.service.gitlab_instance.users.list(username=user)

            if not users_list:
                raise GitlabAPIException(f"Unable to find '{user}' username")

            ids.append(str(users_list[0].id))

        return GitlabIssue.create(
            project=self,
            title=title,
            body=body,
            private=private,
            labels=labels,
            assignees=ids,
        )

    def get_pr(self, pr_id: int) -> PullRequest:
        return GitlabPullRequest.get(project=self, id=pr_id)

    def get_tags(self) -> List["GitTag"]:
        tags = self.gitlab_repo.tags.list()
        return [GitTag(tag.name, tag.commit["id"]) for tag in tags]

    def _git_tag_from_tag_name(self, tag_name: str) -> GitTag:
        git_tag = self.gitlab_repo.tags.get(tag_name)
        return GitTag(name=git_tag.name, commit_sha=git_tag.commit["id"])

    def get_releases(self) -> List[Release]:
        if not hasattr(self.gitlab_repo, "releases"):
            raise OperationNotSupported(
                "This version of python-gitlab does not support release, please upgrade."
            )
        releases = self.gitlab_repo.releases.list(all=True)
        return [
            self._release_from_gitlab_object(
                raw_release=release,
                git_tag=self._git_tag_from_tag_name(release.tag_name),
            )
            for release in releases
        ]

    def get_release(self, identifier=None, name=None, tag_name=None) -> GitlabRelease:
        release = self.gitlab_repo.releases.get(tag_name)
        return self._release_from_gitlab_object(
            raw_release=release, git_tag=self._git_tag_from_tag_name(release.tag_name)
        )

    def create_release(
        self, name: str, tag_name: str, description: str, ref=None
    ) -> GitlabRelease:
        release = self.gitlab_repo.releases.create(
            {"name": name, "tag_name": tag_name, "description": description, "ref": ref}
        )
        return self._release_from_gitlab_object(
            raw_release=release, git_tag=self._git_tag_from_tag_name(release.tag_name)
        )

    def get_latest_release(self) -> GitlabRelease:
        releases = self.gitlab_repo.releases.list()
        # list of releases sorted by released_at
        return self._release_from_gitlab_object(
            raw_release=releases[0],
            git_tag=self._git_tag_from_tag_name(releases[0].tag_name),
        )

    def list_labels(self):
        """
        TODO: Not in API yet.
        Get list of labels in the repository.
        :return: [Label]
        """
        return list(self.gitlab_repo.labels.list())

    def get_forks(self) -> List["GitlabProject"]:
        """
        Get forks of the project.

        :return: [GitlabProject]
        """
        try:
            forks = self.gitlab_repo.forks.list()
        except KeyError:
            # > item = self._data[self._current]
            # > KeyError: 0
            # looks like some API weirdness
            raise OperationNotSupported(
                "Please upgrade python-gitlab to a newer version."
            )
        return [
            GitlabProject(
                repo=fork.path,
                namespace=fork.namespace["full_path"],
                service=self.service,
            )
            for fork in forks
        ]

    def update_labels(self, labels):
        """
        TODO: Not in API yet.
        Update the labels of the repository. (No deletion, only add not existing ones.)

        :param labels: [str]
        :return: int - number of added labels
        """
        current_label_names = [la.name for la in list(self.gitlab_repo.labels.list())]
        changes = 0
        for label in labels:
            if label.name not in current_label_names:
                color = self._normalize_label_color(color=label.color)
                self.gitlab_repo.labels.create(
                    {
                        "name": label.name,
                        "color": color,
                        "description": label.description or "",
                    }
                )

                changes += 1
        return changes

    @staticmethod
    def _normalize_label_color(color):
        if not color.startswith("#"):
            return "#{}".format(color)
        return color

    @staticmethod
    def _commit_comment_from_gitlab_object(raw_comment, commit) -> CommitComment:
        return CommitComment(
            sha=commit, comment=raw_comment.note, author=raw_comment.author["username"]
        )

    def _release_from_gitlab_object(
        self, raw_release, git_tag: GitTag
    ) -> GitlabRelease:
        return GitlabRelease(
            tag_name=raw_release.tag_name,
            url=None,
            created_at=raw_release.created_at,
            tarball_url=raw_release.assets["sources"][1]["url"],
            git_tag=git_tag,
            project=self,
            raw_release=raw_release,
        )

    def get_web_url(self) -> str:
        """
        Get web URL of the project.

        :return: str
        """
        return self.gitlab_repo.web_url

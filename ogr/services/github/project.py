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
from typing import Optional, Dict, List, Set, Union

import github
from github import UnknownObjectException
from github.Repository import Repository
from github.CommitComment import CommitComment as GithubCommitComment
from github.GitRelease import GitRelease as PyGithubRelease

from ogr.abstract import (
    Issue,
    IssueStatus,
    PullRequest,
    PRStatus,
    Release,
    CommitComment,
    GitTag,
    CommitFlag,
    CommitStatus,
    AccessLevel,
)
from ogr.exceptions import GithubAPIException
from ogr.read_only import if_readonly, GitProjectReadOnly
from ogr.services import github as ogr_github
from ogr.services.base import BaseGitProject
from ogr.services.github.flag import GithubCommitFlag
from ogr.services.github.issue import GithubIssue
from ogr.services.github.pull_request import GithubPullRequest
from ogr.services.github.release import GithubRelease
from ogr.utils import filter_paths

logger = logging.getLogger(__name__)


class GithubProject(BaseGitProject):
    service: "ogr_github.GithubService"
    # Permission levels that can merge PRs
    CAN_MERGE_PERMS = ["admin", "write"]

    def __init__(
        self,
        repo: str,
        service: "ogr_github.GithubService",
        namespace: str,
        github_repo: Repository = None,
        read_only: bool = False,
        **unprocess_kwargs,
    ) -> None:
        if unprocess_kwargs:
            logger.warning(
                f"GithubProject will not process these kwargs: {unprocess_kwargs}"
            )
        super().__init__(repo, service, namespace)
        self._github_repo = github_repo
        self.read_only = read_only

        self._github_instance = None

    @property
    def github_instance(self):
        if not self._github_instance:
            self._github_instance = self.service.get_pygithub_instance(
                self.namespace, self.repo
            )

        return self._github_instance

    @property
    def github_repo(self):
        if not self._github_repo:
            self._github_repo = self.github_instance.get_repo(
                full_name_or_id=f"{self.namespace}/{self.repo}"
            )
        return self._github_repo

    def __str__(self) -> str:
        return f'GithubProject(namespace="{self.namespace}", repo="{self.repo}")'

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, GithubProject):
            return False

        return (
            self.repo == o.repo
            and self.namespace == o.namespace
            and self.service == o.service
            and self.read_only == o.read_only
        )

    def _construct_fork_project(self) -> Optional["GithubProject"]:
        gh_user = self.github_instance.get_user()
        user_login = gh_user.login
        try:
            project = GithubProject(
                self.repo, self.service, namespace=user_login, read_only=self.read_only
            )
            if not project.github_repo:
                # The github_repo attribute is lazy.
                return None
            return project
        except github.GithubException as ex:
            logger.debug(f"Project {self.repo}/{user_login} does not exist: {ex}")
            return None

    def exists(self) -> bool:
        try:
            _ = self.github_repo
            return True
        except UnknownObjectException as ex:
            if "Not Found" in str(ex):
                return False
            raise GithubAPIException from ex

    def is_private(self) -> bool:
        """
        Is this repo private? (accessible only by users with granted access)

        :return: if yes, return True
        """
        return self.github_repo.private

    def is_forked(self) -> bool:
        """
        Is this repo forked by the authenticated user?

        :return: if yes, return True
        """
        return bool(self._construct_fork_project())

    @property
    def is_fork(self) -> bool:
        """
        Is this repository a fork?

        :return: True if it is
        """
        return self.github_repo.fork

    @property
    def parent(self) -> Optional["GithubProject"]:
        """
        Return parent project if this project is a fork, otherwise return None
        """
        return (
            self.service.get_project_from_github_repository(self.github_repo.parent)
            if self.is_fork
            else None
        )

    @property
    def default_branch(self):
        return self.github_repo.default_branch

    def get_branches(self) -> List[str]:
        return [branch.name for branch in self.github_repo.get_branches()]

    def get_description(self) -> str:
        return self.github_repo.description

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        """
        AccessLevel.pull => Pull
        AccessLevel.triage => Triage
        AccessLevel.push => Push
        AccessLevel.admin => Admin
        AccessLevel.maintain => Maintain
        """
        access_dict = {
            AccessLevel.pull: "Pull",
            AccessLevel.triage: "Triage",
            AccessLevel.push: "Push",
            AccessLevel.admin: "Admin",
            AccessLevel.maintain: "Maintain",
        }
        try:
            invitation = self.github_repo.add_to_collaborators(
                user, permission=access_dict[access_level]
            )
        except Exception:
            raise GithubAPIException("User {user} not found")

        if invitation is None:
            raise GithubAPIException("User already added")

    def request_access(self):
        raise NotImplementedError("Not possible on GitHub")

    def get_fork(self, create: bool = True) -> Optional["GithubProject"]:
        """
        Provide GithubProject instance of a fork of this project.

        Returns None if this is a fork.

        :param create: create a fork if it doesn't exist
        :return: instance of GithubProject
        """
        username = self.service.user.get_username()
        for fork in self.get_forks():
            if fork.github_repo.owner.login == username:
                return fork

        if not self.is_forked():
            if create:
                return self.fork_create()
            else:
                logger.info(
                    f"Fork of {self.github_repo.full_name}"
                    " does not exist and we were asked not to create it."
                )
                return None
        return self._construct_fork_project()

    def get_owners(self) -> List[str]:
        # in case of github, repository has only one owner
        return [self.github_repo.owner.login]

    def __get_collaborators(self) -> Set[str]:
        try:
            collaborators = self._get_collaborators_with_permission()
        except github.GithubException:
            logger.debug(
                "Current Github token must have push access to view repository permissions."
            )
            return set()

        usernames = []
        for login, permission in collaborators.items():
            if permission in self.CAN_MERGE_PERMS:
                usernames.append(login)

        return set(usernames)

    def who_can_close_issue(self) -> Set[str]:
        return self.__get_collaborators()

    def who_can_merge_pr(self) -> Set[str]:
        return self.__get_collaborators()

    def can_merge_pr(self, username) -> bool:
        return (
            self.github_repo.get_collaborator_permission(username)
            in self.CAN_MERGE_PERMS
        )

    def _get_collaborators_with_permission(self) -> dict:
        """
        Get all project collaborators in dictionary with permission association
        :return: List of usernames
        """
        collaborators = {}
        users = self.github_repo.get_collaborators()
        for user in users:
            permission = self.github_repo.get_collaborator_permission(user)
            collaborators[user.login] = permission
        return collaborators

    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List[Issue]:
        return GithubIssue.get_list(
            project=self, status=status, author=author, assignee=assignee, labels=labels
        )

    def get_issue(self, issue_id: int) -> Issue:
        return GithubIssue.get(project=self, id=issue_id)

    def create_issue(
        self,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Issue:
        if private:
            raise NotImplementedError("Private issues are not supported by Github")
        return GithubIssue.create(
            project=self, title=title, body=body, labels=labels, assignees=assignees
        )

    def delete(self) -> None:
        self.github_repo.delete()

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List[PullRequest]:
        return GithubPullRequest.get_list(project=self, status=status)

    def get_pr(self, pr_id: int) -> PullRequest:
        return GithubPullRequest.get(project=self, id=pr_id)

    def get_sha_from_tag(self, tag_name: str) -> str:
        # TODO: This is ugly. Can we do it better?
        all_tags = self.github_repo.get_tags()
        for tag in all_tags:
            if tag.name == tag_name:
                return tag.commit.sha
        raise GithubAPIException(f"Tag {tag_name} was not found.")

    def get_tag_from_tag_name(self, tag_name: str) -> Optional[GitTag]:
        all_tags = self.github_repo.get_tags()
        for tag in all_tags:
            if tag.name == tag_name:
                return GitTag(name=tag.name, commit_sha=tag.commit.sha)
        return None

    @if_readonly(return_function=GitProjectReadOnly.create_pr)
    def create_pr(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> PullRequest:
        return GithubPullRequest.create(
            project=self,
            title=title,
            body=body,
            target_branch=target_branch,
            source_branch=source_branch,
            fork_username=fork_username,
        )

    @if_readonly(
        return_function=GitProjectReadOnly.commit_comment,
        log_message="Create Comment to commit",
    )
    def commit_comment(
        self, commit: str, body: str, filename: str = None, row: int = None
    ) -> CommitComment:
        """
        Create comment on a commit.

        :param commit: str The SHA of the commit needing a comment.
        :param body: str The text of the comment
        :param filename: str The relative path to the file that necessitates a comment
        :param row: int Line index in the diff to comment on.
        :return: CommitComment
        """
        github_commit = self.github_repo.get_commit(commit)
        if filename and row:
            comment = github_commit.create_comment(
                body=body, position=row, path=filename
            )
        else:
            comment = github_commit.create_comment(body=body)
        return self._commitcomment_from_github_object(comment)

    @if_readonly(
        return_function=GitProjectReadOnly.set_commit_status,
        log_message="Create a status on a commit",
    )
    def set_commit_status(
        self,
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ):
        """
        Create a status on a commit

        :param commit: The SHA of the commit.
        :param state: The state of the status.
        :param target_url: The target URL to associate with this status.
        :param description: A short description of the status
        :param context: A label to differentiate this status from the status of other systems.
        :param trim: bool Whether to trim the description in order to avoid throwing
            github.GithubException
        :return:
        """
        return GithubCommitFlag.set(
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
        Get status of the commit.

        :param commit: str
        :return: [CommitFlag]
        """
        return GithubCommitFlag.get(project=self, commit=commit)

    def get_git_urls(self) -> Dict[str, str]:
        return {"git": self.github_repo.clone_url, "ssh": self.github_repo.ssh_url}

    @if_readonly(return_function=GitProjectReadOnly.fork_create)
    def fork_create(self) -> "GithubProject":
        """
        Fork this project using the authenticated user.
        This may raise an exception if the fork already exists.

        :return: fork GithubProject instance
        """
        gh_user = self.github_instance.get_user()
        return self.service.get_project_from_github_repository(
            gh_user.create_fork(self.github_repo)
        )

    def change_token(self, new_token: str):
        raise NotImplementedError

    def get_file_content(self, path: str, ref=None) -> str:
        ref = ref or self.default_branch
        try:
            return self.github_repo.get_contents(
                path=path, ref=ref
            ).decoded_content.decode()
        except UnknownObjectException as ex:
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
        paths = []
        contents = self.github_repo.get_contents(path="", ref=ref)

        if recursive:
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(
                        self.github_repo.get_contents(path=file_content.path, ref=ref)
                    )
                else:
                    paths.append(file_content.path)

        else:
            paths = [
                file_content.path
                for file_content in contents
                if file_content.type != "dir"
            ]

        if filter_regex:
            paths = filter_paths(paths, filter_regex)

        return paths

    def _release_from_github_object(
        self, raw_release: PyGithubRelease, git_tag: GitTag
    ) -> GithubRelease:
        """
        Get ogr.abstract.Release object from github.GithubRelease

        :param raw_release: GithubRelease, object from Github API
            https://developer.github.com/v3/repos/releases/
        :return: Release, example(type, value):
            tag_name: str, "v1.0.0"
            url: str, "https://api.github.com/repos/octocat/Hello-World/releases/1"
            created_at: datetime.datetime, 2018-09-19 12:56:26
            tarball_url: str, "https://api.github.com/repos/octocat/Hello-World/tarball/v1.0.0"
            git_tag: GitTag
            project: GithubProject
            raw_release: PyGithubRelease
        """
        return GithubRelease(
            tag_name=raw_release.tag_name,
            url=raw_release.url,
            created_at=str(raw_release.created_at),
            tarball_url=raw_release.tarball_url,
            git_tag=git_tag,
            project=self,
            raw_release=raw_release,
        )

    @staticmethod
    def _commitcomment_from_github_object(
        raw_commitcoment: GithubCommitComment,
    ) -> CommitComment:
        return CommitComment(
            comment=raw_commitcoment.body,
            author=raw_commitcoment.user.login,
            sha=raw_commitcoment.commit_id,
        )

    def get_labels(self):
        """
        Get list of labels in the repository.
        :return: [Label]
        """
        return list(self.github_repo.get_labels())

    def update_labels(self, labels):
        """
        Update the labels of the repository. (No deletion, only add not existing ones.)

        :param labels: [str]
        :return: int - number of added labels
        """
        current_label_names = [la.name for la in list(self.github_repo.get_labels())]
        changes = 0
        for label in labels:
            if label.name not in current_label_names:
                color = self._normalize_label_color(color=label.color)
                self.github_repo.create_label(
                    name=label.name, color=color, description=label.description or ""
                )

                changes += 1
        return changes

    @staticmethod
    def _normalize_label_color(color):
        if color.startswith("#"):
            return color[1:]
        return color

    def _release_id_from_name(self, name) -> Optional[int]:
        releases = self.github_repo.get_releases()
        for release in releases:
            if release.title == name:
                return release.id
        return None

    def _release_id_from_tag(self, tag) -> Optional[int]:
        releases = self.github_repo.get_releases()
        for release in releases:
            if release.tag_name == tag:
                return release.id
        return None

    def get_release(self, identifier=None, name=None, tag_name=None) -> GithubRelease:
        if tag_name:
            identifier = self._release_id_from_tag(tag_name)
        elif name:
            identifier = self._release_id_from_name(name)
        if identifier is None:
            raise GithubAPIException("Release was not found.")
        release = self.github_repo.get_release(id=identifier)
        return self._release_from_github_object(
            raw_release=release, git_tag=self.get_tag_from_tag_name(release.tag_name)
        )

    def get_latest_release(self) -> GithubRelease:
        release = self.github_repo.get_latest_release()
        return self._release_from_github_object(
            raw_release=release, git_tag=self.get_tag_from_tag_name(release.tag_name)
        )

    def get_releases(self) -> List[Release]:
        releases = self.github_repo.get_releases()
        return [
            self._release_from_github_object(
                raw_release=release,
                git_tag=self.get_tag_from_tag_name(release.tag_name),
            )
            for release in releases
        ]

    def create_release(self, tag: str, name: str, message: str) -> GithubRelease:
        created_release = self.github_repo.create_git_release(
            tag=tag, name=name, message=message
        )
        return self.get_release(created_release.id)

    def get_forks(self) -> List["GithubProject"]:
        """
        Get forks of the project.

        :return: [PagureProject]
        """
        return [
            self.service.get_project_from_github_repository(fork)
            for fork in self.github_repo.get_forks()
            if fork.owner
        ]

    def get_web_url(self) -> str:
        """
        Get web URL of the project.

        :return: str
        """
        return self.github_repo.html_url

    def get_tags(self) -> List["GitTag"]:
        return [GitTag(tag.name, tag.commit.sha) for tag in self.github_repo.get_tags()]

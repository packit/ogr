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
from typing import List, Optional, Dict, Set

import gitlab
from gitlab.v4.objects import Project as GitlabObjectsProject

from ogr.abstract import (
    GitService,
    GitUser,
    PullRequest,
    Issue,
    Release,
    IssueComment,
    PRComment,
    GitTag,
    IssueStatus,
    CommitFlag,
    PRStatus,
    CommitComment,
)
from ogr.exceptions import GitlabAPIException
from ogr.factory import use_for_service
from ogr.services.base import BaseGitProject, BaseGitUser

logger = logging.getLogger(__name__)


class GitlabRelease(Release):
    project: "GitlabProject"

    def __init__(
        self,
        tag_name: str,
        url: Optional[str],
        created_at: str,
        tarball_url: str,
        git_tag: GitTag,
        project: "GitlabProject",
        raw_release,
    ) -> None:
        super().__init__(tag_name, url, created_at, tarball_url, git_tag, project)
        self.raw_release = raw_release

    @property
    def title(self):
        return self.raw_release.name

    @property
    def body(self):
        return self.raw_release.description


@use_for_service("gitlab")
class GitlabService(GitService):
    name = "gitlab"

    def __init__(self, token=None, instance_url=None, ssl_verify=True):
        super().__init__(token=token)
        self.instance_url = instance_url or "https://gitlab.com"
        self.token = token
        self.ssl_verify = ssl_verify
        self._gitlab_instance = None

    @property
    def gitlab_instance(self) -> gitlab.Gitlab:
        if not self._gitlab_instance:
            self._gitlab_instance = gitlab.Gitlab(
                url=self.instance_url,
                private_token=self.token,
                ssl_verify=self.ssl_verify,
            )
            self._gitlab_instance.auth()
        return self._gitlab_instance

    @property
    def user(self) -> GitUser:
        return GitlabUser(service=self)

    def __str__(self) -> str:
        token_str = f", token='{self.token}'" if self.token else ""
        str_result = (
            f"GitlabService(instance_url='{self.instance_url}'"
            f"{token_str}, "
            f"ssl_verify={self.ssl_verify})"
        )
        return str_result

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, GitlabService):
            return False

        return (
            self.token == o.token  # type: ignore
            and self.instance_url == o.instance_url  # type: ignore
            and self.ssl_verify == o.ssl_verify  # type: ignore
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def get_project(
        self, repo=None, namespace=None, is_fork=False, **kwargs
    ) -> "GitlabProject":
        if is_fork:
            namespace = self.user.get_username()
        return GitlabProject(repo=repo, namespace=namespace, service=self, **kwargs)

    def change_token(self, new_token: str) -> None:
        self.token = new_token
        self._gitlab_instance = None

    def project_create(self, repo: str, namespace: str = None) -> "GitlabProject":
        data = {"name": repo}
        if namespace:
            try:
                group = self.gitlab_instance.groups.get(namespace)
            except gitlab.GitlabGetError:
                raise GitlabAPIException(f"Group {namespace} not found.")
            data["namespace_id"] = group.id
        new_project = self.gitlab_instance.projects.create(data)
        return GitlabProject(
            repo=repo, namespace=namespace, service=self, gitlab_repo=new_project
        )


class GitlabProject(BaseGitProject):
    service: GitlabService

    def __init__(
        self,
        repo: str,
        service: GitlabService,
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

    def can_close_issue(self, username: str, issue: Issue) -> bool:
        allowed_users = self.who_can_close_issue()

        if username in allowed_users or username == issue.author:
            return True

        return False

    def can_merge_pr(self, username) -> bool:
        allowed_users = self.who_can_close_issue()

        if username in allowed_users:
            return True

        return False

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
        return [
            member.username
            for member in self.gitlab_repo.members.all(all=True)
            if member.access_level in access_levels
        ]

    def get_issue_comments(
        self, issue_id, filter_regex: str = None, reverse: bool = False
    ) -> List["IssueComment"]:
        raise NotImplementedError()

    def issue_close(self, issue_id: int) -> Issue:
        issue = self.gitlab_repo.issues.get(issue_id)
        issue.state_event = "close"
        issue.save()
        return self._issue_from_gitlab_object(issue)

    def get_issue_labels(self, issue_id: int) -> List[str]:
        try:
            issue = self.gitlab_repo.issues.get(issue_id)
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Issue {issue_id} was not found.")
            raise GitlabAPIException(f"Issue {issue_id} was not found. ", ex)
        return issue.labels

    def add_issue_labels(self, issue_id, labels) -> None:
        try:
            issue = self.gitlab_repo.issues.get(issue_id)
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Issue {issue_id} was not found.")
            raise GitlabAPIException(f"Issue {issue_id} was not found. ", ex)
        for label in labels:
            issue.labels.append(label)
        issue.save()

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List["PullRequest"]:
        # Gitlab API has status 'opened', not 'open'
        mrs = self.gitlab_repo.mergerequests.list(
            state=status.name if status != PRStatus.open else "opened",
            order_by="updated_at",
            sort="desc",
        )
        return [self._pr_from_gitlab_object(mr) for mr in mrs]

    def get_sha_from_tag(self, tag_name: str) -> str:
        try:
            tag = self.gitlab_repo.tags.get(tag_name)
            return tag.attributes["commit"]["id"]
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Tag {tag_name} was not found.")
            raise GitlabAPIException(f"Tag {tag_name} was not found.", ex)

    def pr_create(
        self, title: str, body: str, target_branch: str, source_branch: str
    ) -> "PullRequest":
        mr = self.gitlab_repo.mergerequests.create(
            {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": body,
            }
        )
        return self._pr_from_gitlab_object(mr)

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
        self, commit: str, state: str, target_url: str, description: str, context: str
    ) -> "CommitFlag":
        """
        Create a status on a commit

        :param commit: The SHA of the commit.
        :param state: The state of the status.
        :param target_url: The target URL to associate with this status.
        :param description: A short description of the status
        :param context: A label to differentiate this status from the status of other systems.
        :return: CommitFlag
        """
        try:
            commit_object = self.gitlab_repo.commits.get(commit)
        except gitlab.exceptions.GitlabGetError:
            logger.error(f"Commit {commit} was not found.")
            raise GitlabAPIException(f"Commit {commit} was not found.")

        data_dict = {
            "state": state,
            "target_url": target_url,
            "context": context,
            "description": description,
        }
        raw_status = commit_object.statuses.create(data_dict)
        return self._commit_status_from_gitlab_object(raw_status)

    def get_commit_statuses(self, commit: str) -> List[CommitFlag]:
        """
        Get the statuses of a commit in a project.
        :param commit: The SHA of the commit.
        :return: [CommitFlag]
        """
        try:
            commit_object = self.gitlab_repo.commits.get(commit)
        except gitlab.exceptions.GitlabGetError:
            logger.error(f"Commit {commit} was not found.")
            raise GitlabAPIException(f"Commit {commit} was not found.")

        raw_statuses = commit_object.statuses.list()
        return [
            self._commit_status_from_gitlab_object(raw_status)
            for raw_status in raw_statuses
        ]

    def pr_close(self, pr_id: int) -> "PullRequest":
        pr = self.gitlab_repo.mergerequests.get(pr_id)
        pr.state_event = "close"
        pr.save()
        return self._pr_from_gitlab_object(pr)

    def pr_merge(self, pr_id: int) -> "PullRequest":
        pr = self.gitlab_repo.mergerequests.get(pr_id)
        pr.merge()
        return self._pr_from_gitlab_object(pr)

    def get_pr_labels(self, pr_id: int) -> List[str]:
        try:
            pr = self.gitlab_repo.mergerequests.get(pr_id)
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"PR {pr_id} was not found.")
            raise GitlabAPIException(f"PR {pr_id} was not found. ", ex)
        return pr.labels

    def add_pr_labels(self, pr_id, labels) -> None:
        try:
            pr = self.gitlab_repo.mergerequests.get(pr_id)
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"PR {pr_id} was not found.")
            raise GitlabAPIException(f"PR {pr_id} was not found. ", ex)
        for label in labels:
            pr.labels.append(label)
        pr.save()

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
        return [branch.name for branch in self.gitlab_repo.branches.list()]

    def get_file_content(self, path, ref="master") -> str:
        try:
            file = self.gitlab_repo.files.get(file_path=path, ref=ref)
            return str(file.decode())
        except gitlab.exceptions.GitlabGetError as ex:
            raise FileNotFoundError(f"File '{path}' on {ref} not found", ex)

    def get_issue_list(self, status: IssueStatus = IssueStatus.open) -> List[Issue]:
        # Gitlab API has status 'opened', not 'open'
        issues = self.gitlab_repo.issues.list(
            state=status.name if status != IssueStatus.open else "opened",
            order_by="updated_at",
            sort="desc",
        )
        return [self._issue_from_gitlab_object(issue) for issue in issues]

    def get_issue_info(self, issue_id: int) -> Issue:
        issue = self.gitlab_repo.issues.get(issue_id)
        return self._issue_from_gitlab_object(gitlab_issue=issue)

    def create_issue(self, title: str, description: str) -> Issue:
        issue = self.gitlab_repo.issues.create(
            {"title": title, "description": description}
        )
        return self._issue_from_gitlab_object(issue)

    def _get_all_issue_comments(self, issue_id: int) -> List[IssueComment]:
        issue = self.gitlab_repo.issues.get(issue_id)
        return [
            self._issuecomment_from_gitlab_object(raw_comment)
            for raw_comment in issue.notes.list()
        ]

    def issue_comment(self, issue_id: int, body: str) -> IssueComment:
        """
        Create comment on an issue.
        """
        issue = self.gitlab_repo.issues.get(issue_id)
        comment = issue.notes.create({"body": body})
        return self._issuecomment_from_gitlab_object(comment)

    def get_pr_info(self, pr_id: int) -> PullRequest:
        mr = self.gitlab_repo.mergerequests.get(pr_id)
        return self._pr_from_gitlab_object(mr)

    def update_pr_info(
        self, pr_id: int, title: str = None, description: str = None
    ) -> PullRequest:
        pr = self.gitlab_repo.mergerequests.get(pr_id)

        if title:
            pr.title = title
        if description:
            pr.description = description

        pr.save()
        return self._pr_from_gitlab_object(pr)

    def get_all_pr_commits(self, pr_id: int) -> List[str]:
        mr = self.gitlab_repo.mergerequests.get(pr_id)
        return [commit.id for commit in mr.commits()]

    def _get_all_pr_comments(self, pr_id: int) -> List[PRComment]:
        pr = self.gitlab_repo.mergerequests.get(pr_id)
        return [
            self._prcomment_from_gitlab_object(raw_comment)
            for raw_comment in pr.notes.list()
        ]

    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
    ) -> PRComment:
        """
        Create comment on an pr.
        """
        pr = self.gitlab_repo.issues.get(pr_id)
        comment = pr.notes.create({"body": body})
        return self._prcomment_from_gitlab_object(comment)

    def get_tags(self) -> List["GitTag"]:
        tags = self.gitlab_repo.tags.list()
        return [GitTag(tag.name, tag.commit["id"]) for tag in tags]

    def _git_tag_from_tag_name(self, tag_name: str) -> GitTag:
        git_tag = self.gitlab_repo.tags.get(tag_name)
        return GitTag(name=git_tag.name, commit_sha=git_tag.commit["id"])

    def get_releases(self) -> List[Release]:
        releases = self.gitlab_repo.releases.list()
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
        fork_objects = [
            GitlabProject(
                repo=fork.path,
                namespace=fork.namespace["full_path"],
                service=self.service,
            )
            for fork in self.gitlab_repo.forks.list()
        ]
        return fork_objects

    def update_labels(self, labels):
        """
        TODO: Not in API yet.
        Update the labels of the repository. (No deletion, only add not existing ones.)

        :param labels: [str]
        :return: int - number of added labels
        """
        current_label_names = [l.name for l in list(self.gitlab_repo.labels.list())]
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
    def _issue_from_gitlab_object(gitlab_issue) -> Issue:
        return Issue(
            title=gitlab_issue.title,
            id=gitlab_issue.iid,
            url=gitlab_issue.web_url,
            description=gitlab_issue.description,
            status=IssueStatus.open
            if gitlab_issue.state == "opened"
            else IssueStatus[gitlab_issue.state],
            author=gitlab_issue.author["username"],
            created=gitlab_issue.created_at,
        )

    @staticmethod
    def _issuecomment_from_gitlab_object(raw_comment) -> IssueComment:
        return IssueComment(
            comment=raw_comment.body,
            author=raw_comment.author["username"],
            created=raw_comment.created_at,
            edited=raw_comment.updated_at,
        )

    @staticmethod
    def _pr_from_gitlab_object(gitlab_pr) -> PullRequest:
        return PullRequest(
            title=gitlab_pr.title,
            id=gitlab_pr.iid,
            status=PRStatus.open
            if gitlab_pr.state == "opened"
            else PRStatus[gitlab_pr.state],
            url=gitlab_pr.web_url,
            description=gitlab_pr.description,
            author=gitlab_pr.author["username"],
            source_branch=gitlab_pr.source_branch,
            target_branch=gitlab_pr.target_branch,
            created=gitlab_pr.created_at,
        )

    @staticmethod
    def _prcomment_from_gitlab_object(raw_comment) -> PRComment:
        return PRComment(
            comment=raw_comment.body,
            author=raw_comment.author["username"],
            created=raw_comment.created_at,
            edited=raw_comment.updated_at,
        )

    @staticmethod
    def _commit_status_from_gitlab_object(raw_status) -> CommitFlag:
        return CommitFlag(
            commit=raw_status.sha,
            state=raw_status.status,
            context=raw_status.name,
            comment=raw_status.description,
            uid=raw_status.id,
            url=raw_status.target_url,
        )

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


class GitlabUser(BaseGitUser):
    service: GitlabService

    def __init__(self, service: GitlabService) -> None:
        super().__init__(service=service)

    def __str__(self) -> str:
        return f'Gitlab(username="{self.get_username()}")'

    @property
    def _gitlab_user(self):
        return self.service.gitlab_instance.user

    def get_username(self) -> str:
        return self._gitlab_user.username

    def get_email(self) -> str:
        return self._gitlab_user.email

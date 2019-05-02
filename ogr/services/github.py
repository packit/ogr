import logging
from typing import Optional, Dict, List, Type

import github
from github import (
    UnknownObjectException,
    IssueComment as GithubIssueComment,
    Repository,
    CommitComment as GithubCommitComment,
)
from github.GitRelease import GitRelease as GithubRelease
from github.PullRequest import PullRequest as GithubPullRequest

from ogr.abstract import (
    GitUser,
    PullRequest,
    PRComment,
    PRStatus,
    Release,
    CommitComment,
    CommitStatus,
)
from ogr.services.base import BaseGitService, BaseGitProject, BaseGitUser
from ogr.mock_core import readonly, GitProjectReadOnly, PersistentObjectStorage
from ogr.services.mock.github_mock import get_Github_class

logger = logging.getLogger(__name__)


class GithubService(BaseGitService):
    # class parameter could be use to mock Github class api
    github_class: Type[github.Github]
    persistent_storage: Optional[PersistentObjectStorage] = None

    def __init__(
        self,
        token=None,
        read_only=False,
        persistent_storage: Optional[PersistentObjectStorage] = None,
    ):
        super().__init__()
        self._token = token
        # it could be set as class parameter too, could be used for mocking in other projects
        if persistent_storage:
            self.persistent_storage = persistent_storage
        if self.persistent_storage:
            self.github_class = get_Github_class(self.persistent_storage)
        else:
            self.github_class = github.Github
        self.github = self.github_class(login_or_token=self._token)
        self.read_only = read_only

    def get_project(
        self, repo=None, namespace=None, is_fork=False, **kwargs
    ) -> "GithubProject":
        if is_fork:
            namespace = self.user.get_username()
        return GithubProject(
            repo=repo,
            namespace=namespace,
            service=self,
            read_only=self.read_only,
            **kwargs,
        )

    @property
    def user(self) -> GitUser:
        return GithubUser(service=self)

    def change_token(self, new_token: str) -> None:
        self._token = new_token
        self.github = github.Github(login_or_token=self._token)


class GithubProject(BaseGitProject):
    service: GithubService

    def __init__(
        self,
        repo: str,
        service: GithubService,
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
        if github_repo:
            self.github_repo = github_repo
        else:
            self.github_repo = service.github.get_repo(
                full_name_or_id=f"{namespace}/{repo}"
            )
        self.read_only = read_only

    def _construct_fork_project(self) -> Optional["GithubProject"]:
        gh_user = self.service.github.get_user()
        user_login = gh_user.login
        try:
            return GithubProject(
                self.repo, self.service, namespace=user_login, read_only=self.read_only
            )
        except github.GithubException as ex:
            logger.debug(f"Project {self.repo}/{user_login} does not exist: {ex}")
            return None

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
        if self.is_fork:
            parent = self.github_repo.parent
            return GithubProject(parent.name, self.service, parent.owner.login)
        return None

    def get_branches(self) -> List[str]:
        return [branch.name for branch in self.github_repo.get_branches()]

    def get_description(self) -> str:
        return self.github_repo.description

    def get_fork(self, create: bool = True) -> Optional["GithubProject"]:
        """
        Provide GithubProject instance of a fork of this project.

        Returns None if this is a fork.

        :param create: create a fork if it doesn't exist
        :return: instance of GithubProject
        """
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

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List[PullRequest]:
        prs = self.github_repo.get_pulls(
            state=status.name, sort="updated", direction="desc"
        )
        try:
            return [self._pr_from_github_object(pr) for pr in prs]
        except UnknownObjectException:
            return []

    def get_pr_info(self, pr_id: int) -> PullRequest:
        pr = self.github_repo.get_pull(number=pr_id)
        return self._pr_from_github_object(pr)

    def _get_all_pr_comments(self, pr_id: int) -> List[PRComment]:
        pr = self.github_repo.get_pull(number=pr_id)
        return [
            self._prcomment_from_github_object(raw_comment)
            for raw_comment in pr.get_issue_comments()
        ]

    def get_sha_from_tag(self, tag_name: str) -> str:
        # TODO: This is ugly. Can we do it better?
        all_tags = self.github_repo.get_tags()
        for tag in all_tags:
            if tag.name == tag_name:
                return tag.commit.sha
        return ""

    @readonly(return_function=GitProjectReadOnly.pr_create)
    def pr_create(
        self, title: str, body: str, target_branch: str, source_branch: str
    ) -> PullRequest:
        created_pr = self.github_repo.create_pull(
            title=title, body=body, base=target_branch, head=source_branch
        )
        return self._pr_from_github_object(created_pr)

    @readonly(
        return_function=GitProjectReadOnly.pr_comment,
        log_message="Create Comment to PR",
    )
    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
    ) -> PRComment:
        """
        Create comment on a pull request. If creating pull request review
        comment (bind to specific point in diff), all values need to be filled.

        :param pr_id: int The ID of the pull request
        :param body: str The text of the comment
        :param commit: str The SHA of the commit needing a comment.
        :param filename: str The relative path to the file that necessitates a comment
        :param row: int The position in the diff where you want to add a review comment
            see https://developer.github.com/v3/pulls/comments/#create-a-comment for more info
        :return: PRComment
        """
        github_pr = self.github_repo.get_pull(number=pr_id)
        if not any([commit, filename, row]):
            comment = github_pr.create_issue_comment(body)
        else:
            github_commit = self.github_repo.get_commit(commit)
            comment = github_pr.create_comment(body, github_commit, filename, row)
        return self._prcomment_from_github_object(comment)

    @readonly(
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

    @readonly(
        return_function=GitProjectReadOnly.set_commit_status,
        log_message="Create a status on a commit",
    )
    def set_commit_status(self, commit, state, target_url, description, context):
        """
        Create a status on a commit

        :param commit: The SHA of the commit.
        :param state: The state of the status.
        :param target_url: The target URL to associate with this status.
        :param description: A short description of the status
        :param context: A label to differentiate this status from the status of other systems.
        :return:
        """
        github_commit = self.github_repo.get_commit(commit)
        github_commit.create_status(state, target_url, description, context)
        return CommitStatus(commit, state, context)

    @readonly(return_function=GitProjectReadOnly.pr_close)
    def pr_close(self, pr_id: int) -> PullRequest:
        raise NotImplementedError

    @readonly(return_function=GitProjectReadOnly.pr_merge)
    def pr_merge(self, pr_id: int) -> PullRequest:
        closed_pr = self.github_repo.get_pull(number=pr_id).merge()
        return self._pr_from_github_object(closed_pr)

    def get_git_urls(self) -> Dict[str, str]:
        return {"git": self.github_repo.clone_url, "ssh": self.github_repo.ssh_url}

    @readonly(return_function=GitProjectReadOnly.fork_create)
    def fork_create(self) -> "GithubProject":
        """
        Fork this project using the authenticated user.
        This may raise an exception if the fork already exists.

        :return: fork GithubProject instance
        """
        gh_user = self.service.github.get_user()
        fork = gh_user.create_fork(self.github_repo)
        return GithubProject("", self.service, "", github_repo=fork)

    def change_token(self, new_token: str):
        raise NotImplementedError

    def get_file_content(self, path: str, ref="master") -> str:
        try:
            return self.github_repo.get_contents(
                path=path, ref=ref
            ).decoded_content.decode()
        except Exception as ex:
            raise FileNotFoundError(f"File '{path}' on {ref} not found", ex)

    def _pr_from_github_object(self, github_pr: GithubPullRequest) -> PullRequest:
        return PullRequest(
            title=github_pr.title,
            id=github_pr.id,
            status=PRStatus[github_pr.state],
            url=github_pr.html_url,
            description=github_pr.body,
            author=github_pr.user.name,
            source_branch=github_pr.head.ref,
            target_branch=github_pr.base.ref,
            created=github_pr.created_at,
        )

    @staticmethod
    def _prcomment_from_github_object(raw_comment: GithubIssueComment) -> PRComment:
        return PRComment(
            comment=raw_comment.body,
            author=raw_comment.user.login,
            created=raw_comment.created_at,
            edited=raw_comment.updated_at,
        )

    @staticmethod
    def _release_from_github_object(raw_release: GithubRelease) -> Release:
        """
        Get ogr.abstract.Release object from github.GithubRelease

        :param raw_release: GithubRelease, object from Github API
            https://developer.github.com/v3/repos/releases/
        :return: Release, example(type, value):
            title: str, "0.1.0"
            body: str, "Description of the release"
            tag_name: str, "v1.0.0"
            url: str, "https://api.github.com/repos/octocat/Hello-World/releases/1"
            created_at: datetime.datetime, 2018-09-19 12:56:26
            tarball_url: str, "https://api.github.com/repos/octocat/Hello-World/tarball/v1.0.0"
        """
        return Release(
            title=raw_release.title,
            body=raw_release.body,
            tag_name=raw_release.tag_name,
            url=raw_release.url,
            created_at=raw_release.created_at,
            tarball_url=raw_release.tarball_url,
        )

    @staticmethod
    def _commitcomment_from_github_object(
        raw_commitcoment: GithubCommitComment
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
        current_label_names = [l.name for l in list(self.github_repo.get_labels())]
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

    def get_release(self, identifier: int) -> Release:
        release = self.github_repo.get_release(id=identifier)
        return self._release_from_github_object(raw_release=release)

    def get_releases(self) -> List[Release]:
        releases = self.github_repo.get_releases()
        return [
            self._release_from_github_object(raw_release=release)
            for release in releases
        ]


class GithubUser(BaseGitUser):
    service: GithubService

    def __init__(self, service: GithubService) -> None:
        super().__init__(service=service)

    def get_username(self) -> str:
        return self.service.github.get_user().login

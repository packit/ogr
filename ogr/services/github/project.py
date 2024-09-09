# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import logging
from typing import ClassVar, Optional, Union

import github
from github import UnknownObjectException
from github.Commit import Commit
from github.CommitComment import CommitComment as GithubCommitComment
from github.GithubException import GithubException
from github.Repository import Repository

from ogr.abstract import (
    AccessLevel,
    CommitComment,
    CommitFlag,
    CommitStatus,
    GitTag,
    Issue,
    IssueStatus,
    PRStatus,
    PullRequest,
    Release,
)
from ogr.exceptions import GithubAPIException, OperationNotSupported
from ogr.read_only import GitProjectReadOnly, if_readonly
from ogr.services import github as ogr_github
from ogr.services.base import BaseGitProject
from ogr.services.github.check_run import (
    GithubCheckRun,
    GithubCheckRunOutput,
    GithubCheckRunResult,
    GithubCheckRunStatus,
)
from ogr.services.github.flag import GithubCommitFlag
from ogr.services.github.issue import GithubIssue
from ogr.services.github.pull_request import GithubPullRequest
from ogr.services.github.release import GithubRelease
from ogr.utils import filter_paths, indirect

logger = logging.getLogger(__name__)


class GithubProject(BaseGitProject):
    service: "ogr_github.GithubService"
    # Permission levels that can merge PRs
    CAN_MERGE_PERMS: ClassVar[set[str]] = {"admin", "write"}

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
                f"GithubProject will not process these kwargs: {unprocess_kwargs}",
            )
        super().__init__(repo, service, namespace)
        self._github_repo = github_repo
        self.read_only = read_only

        self._github_instance = None

    @property
    def github_instance(self):
        if not self._github_instance:
            self._github_instance = self.service.get_pygithub_instance(
                self.namespace,
                self.repo,
            )

        return self._github_instance

    @property
    def github_repo(self):
        if not self._github_repo:
            self._github_repo = self.github_instance.get_repo(
                full_name_or_id=f"{self.namespace}/{self.repo}",
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

    @property
    def description(self) -> str:
        return self.github_repo.description

    @description.setter
    def description(self, new_description: str) -> None:
        self.github_repo.edit(description=new_description)

    @property
    def has_issues(self) -> bool:
        return self.github_repo.has_issues

    def _construct_fork_project(self) -> Optional["GithubProject"]:
        gh_user = self.github_instance.get_user()
        user_login = gh_user.login
        try:
            project = GithubProject(
                self.repo,
                self.service,
                namespace=user_login,
                read_only=self.read_only,
            )
            if not project.github_repo:
                # The github_repo attribute is lazy.
                return None
            return project
        except github.GithubException as ex:
            logger.debug(f"Project {user_login}/{self.repo} does not exist: {ex}")
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
        return self.github_repo.private

    def is_forked(self) -> bool:
        return bool(self._construct_fork_project())

    @property
    def is_fork(self) -> bool:
        return self.github_repo.fork

    @property
    def parent(self) -> Optional["GithubProject"]:
        return (
            self.service.get_project_from_github_repository(self.github_repo.parent)
            if self.is_fork
            else None
        )

    @property
    def default_branch(self):
        return self.github_repo.default_branch

    def get_branches(self) -> list[str]:
        return [branch.name for branch in self.github_repo.get_branches()]

    def get_commits(self, ref: Optional[str] = None) -> list[str]:
        ref = ref or self.github_repo.default_branch
        return [commit.sha for commit in self.github_repo.get_commits(sha=ref)]

    def get_description(self) -> str:
        return self.github_repo.description

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        access_dict = {
            AccessLevel.pull: "Pull",
            AccessLevel.triage: "Triage",
            AccessLevel.push: "Push",
            AccessLevel.admin: "Admin",
            AccessLevel.maintain: "Maintain",
        }
        try:
            invitation = self.github_repo.add_to_collaborators(
                user,
                permission=access_dict[access_level],
            )
        except Exception as ex:
            raise GithubAPIException(f"User {user} not found") from ex

        if invitation is None:
            raise GithubAPIException("User already added")

    def request_access(self):
        raise OperationNotSupported("Not possible on GitHub")

    def get_fork(self, create: bool = True) -> Optional["GithubProject"]:
        username = self.service.user.get_username()
        for fork in self.get_forks():
            if fork.github_repo.owner.login == username:
                return fork

        if not self.is_forked():
            if create:
                return self.fork_create()

            logger.info(
                f"Fork of {self.github_repo.full_name}"
                " does not exist and we were asked not to create it.",
            )
            return None
        return self._construct_fork_project()

    def get_owners(self) -> list[str]:
        # in case of github, repository has only one owner
        return [self.github_repo.owner.login]

    def __get_collaborators(self) -> set[str]:
        collaborators = self._get_collaborators_with_permission()

        usernames = []
        for login, permission in collaborators.items():
            if permission in self.CAN_MERGE_PERMS:
                usernames.append(login)

        return set(usernames)

    def who_can_close_issue(self) -> set[str]:
        return self.__get_collaborators()

    def who_can_merge_pr(self) -> set[str]:
        return self.__get_collaborators()

    def can_merge_pr(self, username) -> bool:
        return (
            self.github_repo.get_collaborator_permission(username)
            in self.CAN_MERGE_PERMS
        )

    def _get_collaborators_with_permission(self) -> dict:
        """
        Get all project collaborators in dictionary with permission association.

        Returns:
            Dictionary with logins of collaborators and their permission level.
        """
        collaborators = {}
        users = self.github_repo.get_collaborators()
        for user in users:
            permission = self.github_repo.get_collaborator_permission(user)
            collaborators[user.login] = permission
        return collaborators

    @indirect(GithubIssue.get_list)
    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list[Issue]:
        pass

    @indirect(GithubIssue.get)
    def get_issue(self, issue_id: int) -> Issue:
        pass

    @indirect(GithubIssue.create)
    def create_issue(
        self,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> Issue:
        pass

    def delete(self) -> None:
        self.github_repo.delete()

    @indirect(GithubPullRequest.get_list)
    def get_pr_list(self, status: PRStatus = PRStatus.open) -> list[PullRequest]:
        pass

    @indirect(GithubPullRequest.get)
    def get_pr(self, pr_id: int) -> PullRequest:
        pass

    def get_sha_from_tag(self, tag_name: str) -> str:
        # TODO: This is ugly. Can we do it better?
        all_tags = self.github_repo.get_tags()
        for tag in all_tags:
            if tag.name == tag_name:
                return tag.commit.sha
        raise GithubAPIException(f"Tag {tag_name} was not found.")

    def get_tag_from_tag_name(self, tag_name: str) -> Optional[GitTag]:
        """
        Get a tag based on a tag name.

        Args:
            tag_name: Name of the tag.

        Returns:
            GitTag associated with the given tag name or `None`.
        """
        all_tags = self.github_repo.get_tags()
        for tag in all_tags:
            if tag.name == tag_name:
                return GitTag(name=tag.name, commit_sha=tag.commit.sha)
        return None

    @if_readonly(return_function=GitProjectReadOnly.create_pr)
    @indirect(GithubPullRequest.create)
    def create_pr(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> PullRequest:
        pass

    @if_readonly(
        return_function=GitProjectReadOnly.commit_comment,
        log_message="Create Comment to commit",
    )
    def commit_comment(
        self,
        commit: str,
        body: str,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> CommitComment:
        github_commit: Commit = self.github_repo.get_commit(commit)
        if filename and row:
            comment = github_commit.create_comment(
                body=body,
                position=row,
                path=filename,
            )
        else:
            comment = github_commit.create_comment(body=body)
        return self._commit_comment_from_github_object(comment)

    @staticmethod
    def _commit_comment_from_github_object(
        raw_commit_coment: GithubCommitComment,
    ) -> CommitComment:
        return CommitComment(
            body=raw_commit_coment.body,
            author=raw_commit_coment.user.login,
            sha=raw_commit_coment.commit_id,
        )

    def get_commit_comments(self, commit: str) -> list[CommitComment]:
        github_commit: Commit = self.github_repo.get_commit(commit)
        return [
            self._commit_comment_from_github_object(comment)
            for comment in github_commit.get_comments()
        ]

    @if_readonly(
        return_function=GitProjectReadOnly.set_commit_status,
        log_message="Create a status on a commit",
    )
    @indirect(GithubCommitFlag.set)
    def set_commit_status(
        self,
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ):
        pass

    @indirect(GithubCommitFlag.get)
    def get_commit_statuses(self, commit: str) -> list[CommitFlag]:
        pass

    @indirect(GithubCheckRun.get)
    def get_check_run(
        self,
        check_run_id: Optional[int] = None,
        commit_sha: Optional[str] = None,
    ) -> Optional["GithubCheckRun"]:
        pass

    @indirect(GithubCheckRun.create)
    def create_check_run(
        self,
        name: str,
        commit_sha: str,
        url: Optional[str] = None,
        external_id: Optional[str] = None,
        status: GithubCheckRunStatus = GithubCheckRunStatus.queued,
        started_at: Optional[datetime.datetime] = None,
        conclusion: Optional[GithubCheckRunResult] = None,
        completed_at: Optional[datetime.datetime] = None,
        output: Optional[GithubCheckRunOutput] = None,
        actions: Optional[list[dict[str, str]]] = None,
    ) -> "GithubCheckRun":
        pass

    @indirect(GithubCheckRun.get_list)
    def get_check_runs(
        self,
        commit_sha: str,
        name: Optional[str] = None,
        status: Optional[GithubCheckRunStatus] = None,
    ) -> list["GithubCheckRun"]:
        pass

    def get_git_urls(self) -> dict[str, str]:
        return {"git": self.github_repo.clone_url, "ssh": self.github_repo.ssh_url}

    @if_readonly(return_function=GitProjectReadOnly.fork_create)
    def fork_create(self, namespace: Optional[str] = None) -> "GithubProject":
        fork_repo = (
            self.github_repo.create_fork(organization=namespace)
            if namespace
            else self.github_repo.create_fork()
        )

        fork = self.service.get_project_from_github_repository(fork_repo)
        logger.debug(f"Forked to {fork.namespace}/{fork.repo}")
        return fork

    def change_token(self, new_token: str):
        raise OperationNotSupported

    def get_file_content(self, path: str, ref=None) -> str:
        ref = ref or self.default_branch
        try:
            return self.github_repo.get_contents(
                path=path,
                ref=ref,
            ).decoded_content.decode()
        except (UnknownObjectException, GithubException) as ex:
            if ex.status == 404:
                raise FileNotFoundError(f"File '{path}' on {ref} not found") from ex
            raise GithubAPIException() from ex

    def get_files(
        self,
        ref: Optional[str] = None,
        filter_regex: Optional[str] = None,
        recursive: bool = False,
    ) -> list[str]:
        ref = ref or self.default_branch
        paths = []
        contents = self.github_repo.get_contents(path="", ref=ref)

        if recursive:
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(
                        self.github_repo.get_contents(path=file_content.path, ref=ref),
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

    def get_labels(self):
        """
        Get list of labels in the repository.

        Returns:
            List of labels in the repository.
        """
        return list(self.github_repo.get_labels())

    def update_labels(self, labels):
        """
        Update the labels of the repository. (No deletion, only add not existing ones.)

        Args:
            labels: List of labels to be added.

        Returns:
            Number of added labels.
        """
        current_label_names = [la.name for la in list(self.github_repo.get_labels())]
        changes = 0
        for label in labels:
            if label.name not in current_label_names:
                color = self._normalize_label_color(color=label.color)
                self.github_repo.create_label(
                    name=label.name,
                    color=color,
                    description=label.description or "",
                )

                changes += 1
        return changes

    @staticmethod
    def _normalize_label_color(color):
        if color.startswith("#"):
            return color[1:]
        return color

    @indirect(GithubRelease.get)
    def get_release(self, identifier=None, name=None, tag_name=None) -> GithubRelease:
        pass

    @indirect(GithubRelease.get_latest)
    def get_latest_release(self) -> Optional[GithubRelease]:
        pass

    @indirect(GithubRelease.get_list)
    def get_releases(self) -> list[Release]:
        pass

    @indirect(GithubRelease.create)
    def create_release(self, tag: str, name: str, message: str) -> GithubRelease:
        pass

    def get_forks(self) -> list["GithubProject"]:
        return [
            self.service.get_project_from_github_repository(fork)
            for fork in self.github_repo.get_forks()
            if fork.owner
        ]

    def get_web_url(self) -> str:
        return self.github_repo.html_url

    def get_tags(self) -> list["GitTag"]:
        return [GitTag(tag.name, tag.commit.sha) for tag in self.github_repo.get_tags()]

    def get_sha_from_branch(self, branch: str) -> Optional[str]:
        try:
            return self.github_repo.get_branch(branch).commit.sha
        except GithubException as ex:
            if ex.status == 404:
                return None
            raise GithubAPIException from ex

    def get_contributors(self) -> set[str]:
        """
        Returns:
            Logins of contributors to the project.
        """
        return {c.login for c in self.github_repo.get_contributors()}

    def users_with_write_access(self) -> set[str]:
        return self.__get_collaborators()

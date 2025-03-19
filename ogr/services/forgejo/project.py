# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging
from collections.abc import Iterable
from functools import cached_property
from typing import Optional, Union

from pyforgejo import NotFoundError, Repository, types

from ogr.abstract import (
    AccessLevel,
    CommitComment,
    CommitFlag,
    CommitStatus,
    GitProject,
    GitTag,
    Issue,
    IssueStatus,
    PRStatus,
    PullRequest,
    Release,
)
from ogr.exceptions import OperationNotSupported
from ogr.services import forgejo
from ogr.services.base import BaseGitProject
from ogr.utils import indirect

from .flag import ForgejoCommitFlag
from .issue import ForgejoIssue
from .pull_request import ForgejoPullRequest
from .release import ForgejoRelease

logger = logging.getLogger(__name__)


class ForgejoProject(BaseGitProject):
    service: "forgejo.ForgejoService"

    def __init__(
        self,
        repo: str,
        service: "forgejo.ForgejoService",
        namespace: str,
        forgejo_repo: Optional[Repository] = None,
        **kwargs,
    ):
        super().__init__(repo, service, namespace)
        self._forgejo_repo = forgejo_repo

    @cached_property
    def forgejo_repo(self) -> types.Repository:
        return self.service.api.repository.repo_get(
            owner=self.namespace,
            repo=self.repo,
        )

    def __str__(self) -> str:
        return (
            f'ForgejoProject(namespace="{self.namespace}", repo="{self.repo}", '
            f"service={self.service})"
        )

    def __eq__(self, o: object) -> bool:
        return (
            isinstance(o, ForgejoProject)
            and self.repo == o.repo
            and self.namespace == o.namespace
            and self.service == o.service
        )

    @property
    def description(self) -> str:
        return self.forgejo_repo.description or ""

    @description.setter
    def description(self, new_description: str) -> None:
        self.service.api.repository.repo_edit(
            owner=self.namespace,
            repo=self.repo,
            description=new_description,
        )

    def delete(self) -> None:
        self.service.api.repository.repo_delete(
            owner=self.namespace,
            repo=self.repo,
        )

    def exists(self) -> bool:
        try:
            _ = self.forgejo_repo
            return True
        except NotFoundError:
            return False

    def is_private(self) -> bool:
        return self.forgejo_repo.private

    def is_forked(self) -> bool:
        return (
            self.forgejo_repo.fork
            and self.forgejo_repo.owner.login == self.service.user.get_username()
        )

    @property
    def is_fork(self) -> bool:
        return self.forgejo_repo.fork

    @property
    def full_repo_name(self) -> str:
        return self.forgejo_repo.full_name

    @property
    def parent(self) -> Optional["GitProject"]:
        if not self.forgejo_repo.parent:
            return None

        return ForgejoProject(
            service=self.service,
            repo=self.forgejo_repo.parent.name,
            namespace=self.forgejo_repo.parent.owner.username,
        )

    @property
    def has_issues(self) -> bool:
        return self.forgejo_repo.has_issues

    def get_branches(self) -> Iterable[str]:
        page = 1
        while branches := self.service.api.repository.repo_list_branches(
            owner=self.namespace,
            repo=self.repo,
            page=page,
        ):
            for branch in branches:
                yield branch.name

            page += 1

    @property
    def default_branch(self) -> str:
        return self.forgejo_repo.default_branch

    def get_commits(self, ref: Optional[str] = None) -> Iterable[str]:
        page = 1
        while commits := self.service.api.repository.repo_get_all_commits(
            owner=self.namespace,
            repo=self.repo,
            sha=ref,
            page=page,
        ):
            for commit in commits:
                yield commit.sha

            page += 1

    def get_description(self) -> str:
        return self.description

    def _construct_fork_project(self) -> Optional["ForgejoProject"]:
        login = self.service.user.get_username()
        try:
            project = ForgejoProject(
                repo=self.repo,
                service=self.service,
                namespace=login,
            )
            _ = project.forgejo_repo
            return project
        except NotFoundError:
            return None

    def get_fork(self, create: bool = True) -> Optional["GitProject"]:
        # The cheapest check that assumes fork has the same repository name as
        # the upstream
        if fork := self._construct_fork_project():
            return fork

        # If not successful, the fork could still exist, but has a custom name
        username = self.service.user.get_username()
        for fork in self.get_forks():
            if fork.forgejo_repo.owner.login == username:
                return fork

        # We have not found any fork owned by the auth'd user
        if create:
            return self.fork_create()

        logger.info(
            f"Fork of {self.forgejo_repo.full_name}"
            " does not exist and we were asked not to create it.",
        )
        return None

    def get_owners(self) -> list[str]:
        """
        Returns:
            List of usernames of project owners.
        """
        raise NotImplementedError("TBD")

    def who_can_close_issue(self) -> set[str]:
        """
        Returns:
            Names of all users who have permission to modify an issue.
        """
        raise NotImplementedError("TBD")

    def who_can_merge_pr(self) -> set[str]:
        """
        Returns:
            Names of all users who have permission to modify pull request.
        """
        raise NotImplementedError("TBD")

    def which_groups_can_merge_pr(self) -> set[str]:
        """
        Returns:
            Names of all groups that have permission to modify pull request.
        """
        raise NotImplementedError("TBD")

    def can_merge_pr(self, username: str) -> bool:
        """
        Args:
            username: Username.

        Returns:
            `True` if user merge pull request, `False` otherwise.
        """
        raise NotImplementedError("TBD")

    def get_users_with_given_access(self, access_levels: list[AccessLevel]) -> set[str]:
        """
        Args:
            access_levels: list of access levels

        Returns:
            set of users with given access levels
        """
        raise NotImplementedError("TBD")

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        """
        Add user to project.

        Args:
            user: Username of the user.
            access_level: Permissions for the user.
        """
        raise NotImplementedError()

    def remove_user(self, user: str) -> None:
        """
        Remove user from project.

        Args:
            user: Username of the user.
        """
        raise NotImplementedError()

    def request_access(self) -> None:
        """
        Request an access to the project (cannot specify access level to be granted;
        needs to be approved and specified by the user with maintainer/admin rights).
        """
        raise NotImplementedError()

    def add_group(self, group: str, access_level: AccessLevel) -> None:
        """
        Add group to project.

        Args:
            group: Name of the group.
            access_level: Permissions for the group.
        """
        raise NotImplementedError()

    def remove_group(self, group: str) -> None:
        """
        Remove group from project.

        Args:
            group: Name of the group.
        """
        raise NotImplementedError()

    @indirect(ForgejoIssue.get_list)
    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list["Issue"]:
        pass

    @indirect(ForgejoIssue.get)
    def get_issue(self, issue_id: int) -> "Issue":
        pass

    @indirect(ForgejoIssue.create)
    def create_issue(
        self,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> Issue:
        pass

    @indirect(ForgejoPullRequest.get_list)
    def get_pr_list(self, status: PRStatus = PRStatus.open) -> list["PullRequest"]:
        pass

    @indirect(ForgejoPullRequest.get)
    def get_pr(self, pr_id: int) -> "PullRequest":
        pass

    def get_pr_files_diff(
        self,
        pr_id: int,
        retries: int = 0,
        wait_seconds: int = 3,
    ) -> dict:
        """
        Get files diff of a pull request.

        Args:
            pr_id: ID of the pull request.

        Returns:
            Dictionary representing files diff.
        """
        # [NOTE] Implemented only for Pagure, for details see
        # https://github.com/packit/ogr/issues/895
        raise NotImplementedError()

    def get_tags(self) -> Iterable["GitTag"]:
        page = 1

        while tags := self.service.api.repository.repo_list_tags(
            owner=self.namespace,
            repo=self.repo,
            page=page,
        ):
            for tag in tags:
                yield GitTag(
                    name=tag.name,
                    commit_sha=tag.commit.sha,
                )

            page += 1

    def get_sha_from_tag(self, tag_name: str) -> str:
        return self.service.api.repo_get_tag(
            owner=self.namespace,
            repo=self.repo,
            tag=tag_name,
        ).commit.sha

    @indirect(ForgejoRelease.get)
    def get_release(
        self,
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> Release:
        pass

    @indirect(ForgejoRelease.get_latest)
    def get_latest_release(self) -> Optional[Release]:
        pass

    @indirect(ForgejoRelease.get_list)
    def get_releases(self) -> list[Release]:
        pass

    @indirect(ForgejoRelease.create)
    def create_release(
        self,
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> Release:
        pass

    @indirect(ForgejoPullRequest.create)
    def create_pr(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> "PullRequest":
        pass

    def commit_comment(
        self,
        commit: str,
        body: str,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "CommitComment":
        raise OperationNotSupported("Forgejo doesn't support commit comments")

    def get_commit_comments(self, commit: str) -> list[CommitComment]:
        raise OperationNotSupported("Forgejo doesn't support commit comments")

    def get_commit_comment(self, commit_sha: str, comment_id: int) -> CommitComment:
        raise OperationNotSupported("Forgejo doesn't support commit comments")

    @indirect(ForgejoCommitFlag.set)
    def set_commit_status(
        self,
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "CommitFlag":
        pass

    @indirect(ForgejoCommitFlag.get)
    def get_commit_statuses(self, commit: str) -> list[CommitFlag]:
        pass

    def get_git_urls(self) -> dict[str, str]:
        return {
            "git": self.forgejo_repo.clone_url,
            "ssh": self.forgejo_repo.ssh_url,
        }

    def fork_create(self, namespace: Optional[str] = None) -> "GitProject":
        if namespace:
            self.service.api.repository.create_fork(
                owner=self.namespace,
                repo=self.repo,
                organization=namespace,
            )
            return ForgejoProject(
                repo=self.repo,
                service=self.service,
                namespace=namespace,
            )

        self.service.api.repository.create_fork(
            owner=self.namespace,
            repo=self.repo,
        )
        return ForgejoProject(
            repo=self.repo,
            service=self.service,
            namespace=self.service.user.get_username(),
        )

    def change_token(self, new_token: str) -> None:
        # [NOTE] API doesn't provide any method to change the token, and it's
        # embedded in the httpx client that's wrapped by pyforgejo wrapper to
        # avoid duplication between sync and async calls…
        raise NotImplementedError(
            "Not possible; requires recreation of the httpx client",
        )

    def get_file_content(self, path: str, ref: Optional[str] = None) -> str:
        try:
            return self.service.api.repository.repo_get_contents(
                owner=self.namespace,
                repo=self.repo,
                filepath=path,
                ref=ref,
            ).content
        except NotFoundError as ex:
            raise FileNotFoundError() from ex

    def get_files(
        self,
        ref: Optional[str] = None,
        filter_regex: Optional[str] = None,
        recursive: bool = False,
    ) -> list[str]:
        """
        Get a list of file paths of the repo.

        Args:
            ref: Branch or commit.

                Defaults to repo's default branch.
            filter_regex: Filter the paths with `re.search`.

                Defaults to `None`, which means no filtering.
            recursive: Whether to return only top directory files
                or all files recursively.

                Defaults to `False`, which means only top-level directory.

        Returns:
            List of paths of the files in the repo.
        """
        # [TODO]
        raise NotImplementedError

    def get_forks(self) -> Iterable["ForgejoProject"]:
        page = 1

        while forks := self.service.api.repository.list_forks(
            owner=self.namespace,
            repo=self.repo,
            page=page,
        ):
            for fork in forks:
                yield ForgejoProject(
                    namespace=fork.owner.login,
                    repo=fork.name,
                    service=self.service,
                )

            page += 1

    def get_web_url(self) -> str:
        return self.forgejo_repo.html_url

    def get_sha_from_branch(self, branch: str) -> Optional[str]:
        try:
            branch_info = self.service.api.repository.repo_get_branch(
                owner=self.namespace,
                repo=self.repo,
                branch=branch,
            )
            return branch_info.commit.id
        except NotFoundError:
            return None

    def get_contributors(self) -> set[str]:
        """
        Returns:
            Set of all contributors to the given project.
        """
        raise NotImplementedError("TBD")

    def users_with_write_access(self) -> set[str]:
        """
        Returns:
            List of users who have write access to the project
        """
        raise NotImplementedError("TBD")

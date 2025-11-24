# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import codecs
import contextlib
import logging
from collections.abc import Iterable
from functools import cached_property, partial
from typing import ClassVar, Optional, Union

from pyforgejo import NotFoundError, Repository, types
from pyforgejo.repository.client import RepositoryClient

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
from ogr.utils import filter_paths, indirect

from .flag import ForgejoCommitFlag
from .issue import ForgejoIssue
from .pull_request import ForgejoPullRequest
from .release import ForgejoRelease
from .utils import paginate

logger = logging.getLogger(__name__)


class ForgejoProject(BaseGitProject):
    service: "forgejo.ForgejoService"
    access_dict: ClassVar[dict] = {
        AccessLevel.pull: "read",
        AccessLevel.triage: "read",
        AccessLevel.push: "write",
        AccessLevel.admin: "admin",
        AccessLevel.maintain: "owner",
        None: "",
    }

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

    @property
    def api(self) -> RepositoryClient:
        """Returns a `RepositoryClient` from pyforgejo. Helper to save some
        typing.
        """
        return self.service.api.repository

    def partial_api(self, method, /, *args, **kwargs):
        """Returns a partial API call for `ForgejoProject`.

        Injects `owner` and `repo` for the calls to `/repository/` endpoints.

        Args:
            method: Specific method on the Pyforgejo API that is to be wrapped.
            *args: Positional arguments that get injected into every call.
            **kwargs: Keyword-arguments that get injected into every call.

        Returns:
            Callable with pre-injected parameters.

        """
        return partial(
            method,
            *args,
            **kwargs,
            owner=self.namespace,
            repo=self.repo,
        )

    @cached_property
    def forgejo_repo(self) -> types.Repository:
        return self.api.repo_get(
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
        self.partial_api(self.api.repo_edit)(description=new_description)

    def delete(self) -> None:
        self.partial_api(self.api.repo_delete)()

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
        return (
            branch.name
            for branch in paginate(
                self.partial_api(self.api.repo_list_branches),
            )
        )

    @property
    def default_branch(self) -> str:
        return self.forgejo_repo.default_branch

    def get_commits(self, ref: Optional[str] = None) -> Iterable[str]:
        return (
            commit.sha
            for commit in paginate(
                self.partial_api(
                    self.api.repo_get_all_commits,
                    sha=ref,
                ),
            )
        )

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
        return [self.forgejo_repo.owner.username]

    def _get_owner_or_org_collaborators(self) -> set[str]:
        namespace = self.get_owners()[0]
        try:
            teams = self.api.repo_list_teams(
                owner=self.namespace,
                repo=self.repo,
            )
        except Exception as ex:
            # no teams, repo owned by regular user
            if "not owned by an organization" in str(ex):
                return {namespace}
            raise

        # repo owned by org, each org can have multiple teams with
        # different levels of access
        collaborators: set[str] = set()
        for team in teams:
            members = self.service.api.organization.org_list_team_members(team.id)
            collaborators.update(user.username for user in members)

        return collaborators

    def _get_collaborators(self) -> list[str]:
        return [
            c.username
            for c in self.api.repo_list_collaborators(
                owner=self.namespace,
                repo=self.repo,
            )
        ] + list(self._get_owner_or_org_collaborators())

    def _get_collaborators_with_access(self) -> dict[str, str]:
        return {
            c: self.api.repo_get_repo_permissions(
                owner=self.namespace,
                repo=self.repo,
                collaborator=c,
            ).permission
            for c in self._get_collaborators()
        }

    def get_contributors(self) -> set[str]:
        return set(self._get_collaborators())

    def users_with_write_access(self) -> set[str]:
        return {
            collaborator
            for collaborator, access in self._get_collaborators_with_access().items()
            if access in ("owner", "admin", "write")
        }

    def who_can_close_issue(self) -> set[str]:
        return self.users_with_write_access()

    def who_can_merge_pr(self) -> set[str]:
        return self.users_with_write_access()

    def can_merge_pr(self, username: str) -> bool:
        return self.api.repo_get_repo_permissions(
            owner=self.namespace,
            repo=self.repo,
            collaborator=username,
        ).permission in ("owner", "admin", "write")

    def get_users_with_given_access(self, access_levels: list[AccessLevel]) -> set[str]:
        access_levels_forgejo = [
            self.access_dict[access_level] for access_level in access_levels
        ]

        return {
            user
            for user, permission in self._get_collaborators_with_access().items()
            if permission in access_levels_forgejo
        }

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        if access_level == AccessLevel.maintain:
            raise OperationNotSupported("Not possible to add a user as `owner`.")

        self.api.repo_add_collaborator(
            owner=self.namespace,
            repo=self.repo,
            collaborator=user,
            permission=self.access_dict[access_level],
        )

    def remove_user(self, user: str) -> None:
        self.api.repo_delete_collaborator(
            owner=self.namespace,
            repo=self.repo,
            collaborator=user,
        )

    def request_access(self) -> None:
        raise OperationNotSupported("Not possible on Forgejo")

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
    def get_pr_list(self, status: PRStatus = PRStatus.open) -> Iterable["PullRequest"]:
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
        return (
            GitTag(
                name=tag.name,
                commit_sha=tag.commit.sha,
            )
            for tag in paginate(self.partial_api(self.api.repo_list_tags))
        )

    def get_sha_from_tag(self, tag_name: str) -> str:
        return self.partial_api(
            self.api.repo_get_tag,
            tag=tag_name,
        )().commit.sha

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
    def get_commit_statuses(self, commit: str) -> Iterable["CommitFlag"]:
        pass

    def get_git_urls(self) -> dict[str, str]:
        return {
            "git": self.forgejo_repo.clone_url,
            "ssh": self.forgejo_repo.ssh_url,
        }

    def fork_create(self, namespace: Optional[str] = None) -> "GitProject":
        if namespace:
            self.api.create_fork(
                owner=self.namespace,
                repo=self.repo,
                organization=namespace,
            )
            return ForgejoProject(
                repo=self.repo,
                service=self.service,
                namespace=namespace,
            )

        self.api.create_fork(
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

    def get_file_content(
        self,
        path: str,
        ref: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> str:
        try:
            remote_file: types.ContentsResponse = self.partial_api(
                self.api.repo_get_contents,
                filepath=path,
                ref=ref,
            )()

            # [NOTE] If you touch this, good luck, have fun…
            # tl;dr ‹ContentsResponse› from the Pyforgejo contains the content
            # of the file that's (I hope always) base64-encoded, but it's stored
            # as a string, so here it's needed to convert the UTF-8 encoded
            # string back to bytes (duh, cause base64 is used for encoding raw
            # data), then decode the base64 bytes to just bytes and then decode
            # those to a UTF-8 string… EWWW…
            return codecs.decode(
                bytes(remote_file.content, "utf-8"),
                encoding=remote_file.encoding,
            ).decode("utf-8")

        except NotFoundError as ex:
            raise FileNotFoundError() from ex

    def __get_files(
        self,
        path: str,
        ref: str,
        recursive: bool,
    ) -> Iterable[str]:
        contents: types.ContentsResponse | list[types.ContentsResponse]

        subdirectories = ["."]

        with contextlib.suppress(IndexError):
            while path := subdirectories.pop():
                contents = self.partial_api(
                    self.api.repo_get_contents,
                    filepath=path,
                    ref=ref,
                )()

                if isinstance(contents, types.ContentsResponse):
                    # singular file, return path and skip any further processing
                    yield contents.path
                    continue

                for file in contents:
                    if file.type == "dir":
                        subdirectories.append(file.path)
                        continue

                    yield file.path

    def get_files(
        self,
        ref: Optional[str] = None,
        filter_regex: Optional[str] = None,
        recursive: bool = False,
    ) -> Iterable[str]:
        logger.warning(
            "‹ForgejoProject.get_files()› method can fail because of incorrect"
            " OpenAPI spec",
        )

        ref = ref or self.default_branch
        paths = self.__get_files(".", ref=ref, recursive=recursive)

        if filter_regex:
            return filter_paths(paths, filter_regex)

        return paths

    def get_forks(self) -> Iterable["ForgejoProject"]:
        return (
            ForgejoProject(
                namespace=fork.owner.login,
                repo=fork.name,
                service=self.service,
            )
            for fork in paginate(
                self.partial_api(self.api.list_forks),
            )
        )

    def get_web_url(self) -> str:
        return self.forgejo_repo.html_url

    def get_sha_from_branch(self, branch: str) -> Optional[str]:
        try:
            branch_info = self.partial_api(
                self.api.repo_get_branch,
                branch=branch,
            )()
            return branch_info.commit.id
        except NotFoundError:
            return None

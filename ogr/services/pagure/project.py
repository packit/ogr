# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging
from collections.abc import Iterable
from typing import ClassVar, Optional
from urllib.parse import urlparse

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
from ogr.exceptions import (
    OgrException,
    OperationNotSupported,
    PagureAPIException,
)
from ogr.read_only import GitProjectReadOnly, if_readonly
from ogr.services import pagure as ogr_pagure
from ogr.services.base import BaseGitProject
from ogr.services.pagure.flag import PagureCommitFlag
from ogr.services.pagure.issue import PagureIssue
from ogr.services.pagure.pull_request import PagurePullRequest
from ogr.services.pagure.release import PagureRelease
from ogr.utils import RequestResponse, filter_paths, indirect

logger = logging.getLogger(__name__)


class PagureProject(BaseGitProject):
    service: "ogr_pagure.PagureService"
    access_dict: ClassVar[dict] = {
        AccessLevel.pull: "ticket",
        AccessLevel.triage: "ticket",
        AccessLevel.push: "commit",
        AccessLevel.admin: "commit",
        AccessLevel.maintain: "admin",
        None: "",
    }

    def __init__(
        self,
        repo: str,
        namespace: Optional[str],
        service: "ogr_pagure.PagureService",
        username: Optional[str] = None,
        is_fork: bool = False,
    ) -> None:
        super().__init__(repo, service, namespace)
        self.read_only = service.read_only

        self._is_fork = is_fork
        self._username = username

        self.repo = repo
        self.namespace = namespace

    def __str__(self) -> str:
        fork_info = ""
        if self._is_fork:
            fork_info = f', username="{self._username}", is_fork={self._is_fork}'
        return f'PagureProject(namespace="{self.namespace}", repo="{self.repo}"{fork_info})'

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, PagureProject):
            return False

        return (
            self.repo == o.repo
            and self.namespace == o.namespace
            and self.service == o.service
            and self._username == o._username
            and self._is_fork == o._is_fork
            and self.read_only == o.read_only
        )

    @property
    def _user(self) -> str:
        if not self._username:
            self._username = self.service.user.get_username()
        return self._username

    def _call_project_api(
        self,
        *args,
        add_fork_part: bool = True,
        add_api_endpoint_part: bool = True,
        method: Optional[str] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict:
        """
        Call project API endpoint.

        Args:
            *args: String parts of the URL, e.g. `"a", "b"` will call `project/a/b`
            add_fork_part: If the project is a fork, use `fork/username` prefix.

                Defaults to `True`.
            add_api_endpoint_part: Add part with API endpoint (`/api/0/`).

                Defaults to `True`.
            method: Method of the HTTP request, e.g. `"GET"`, `"POST"`, etc.
            params: HTTP(S) query parameters in form of a dictionary.
            data: Data to be sent in form of a dictionary.

        Returns:
            Dictionary representing response.
        """
        request_url = self._get_project_url(
            *args,
            add_api_endpoint_part=add_api_endpoint_part,
            add_fork_part=add_fork_part,
        )

        return self.service.call_api(
            url=request_url,
            method=method,
            params=params,
            data=data,
        )

    def _call_project_api_raw(
        self,
        *args,
        add_fork_part: bool = True,
        add_api_endpoint_part: bool = True,
        method: Optional[str] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> RequestResponse:
        """
        Call project API endpoint.

        Args:
            *args: String parts of the URL, e.g. `"a", "b"` will call `project/a/b`
            add_fork_part: If the project is a fork, use `fork/username` prefix.

                Defaults to `True`.
            add_api_endpoint_part: Add part with API endpoint (`/api/0/`).

                Defaults to `True`.
            method: Method of the HTTP request, e.g. `"GET"`, `"POST"`, etc.
            params: HTTP(S) query parameters in form of a dictionary.
            data: Data to be sent in form of a dictionary.

        Returns:
            `RequestResponse` object containing response.
        """
        request_url = self._get_project_url(
            *args,
            add_api_endpoint_part=add_api_endpoint_part,
            add_fork_part=add_fork_part,
        )

        return self.service.call_api_raw(
            url=request_url,
            method=method,
            params=params,
            data=data,
        )

    def _get_project_url(self, *args, add_fork_part=True, add_api_endpoint_part=True):
        additional_parts = []
        if self._is_fork and add_fork_part:
            additional_parts += ["fork", self._user]
        return self.service.get_api_url(
            *additional_parts,
            self.namespace,
            self.repo,
            *args,
            add_api_endpoint_part=add_api_endpoint_part,
        )

    def get_project_info(self):
        return self._call_project_api(method="GET")

    def get_branches(self) -> list[str]:
        return_value = self._call_project_api("git", "branches", method="GET")
        return return_value["branches"]

    @property
    def default_branch(self) -> str:
        return_value = self._call_project_api("git", "branches", method="GET")
        return return_value["default"]

    def get_description(self) -> str:
        return self.get_project_info()["description"]

    @property
    def description(self) -> str:
        return self.get_project_info()["description"]

    @description.setter
    def description(self, new_description: str) -> None:
        raise OperationNotSupported("Not possible on Pagure")

    @property
    def has_issues(self) -> bool:
        options = self._call_project_api("options", method="GET")
        return options["settings"]["issue_tracker"]

    def get_owners(self) -> list[str]:
        project = self.get_project_info()
        return project["access_users"]["owner"]

    def who_can_close_issue(self) -> set[str]:
        users: set[str] = set()
        project = self.get_project_info()
        users.update(project["access_users"]["admin"])
        users.update(project["access_users"]["commit"])
        users.update(project["access_users"]["ticket"])
        users.update(project["access_users"]["owner"])
        return users

    def who_can_merge_pr(self) -> set[str]:
        users: set[str] = set()
        project = self.get_project_info()
        users.update(project["access_users"]["admin"])
        users.update(project["access_users"]["commit"])
        users.update(project["access_users"]["owner"])
        return users

    def which_groups_can_merge_pr(self) -> set[str]:
        groups: set[str] = set()
        project = self.get_project_info()
        groups.update(project["access_groups"]["admin"])
        groups.update(project["access_groups"]["commit"])
        return groups

    def can_merge_pr(self, username) -> bool:
        accounts_that_can_merge_pr = self.who_can_merge_pr()

        groups_that_can_merge_pr = self.which_groups_can_merge_pr()
        accounts_that_can_merge_pr.update(
            member
            for group in groups_that_can_merge_pr
            for member in self.service.get_group(group).members
        )

        logger.info(
            f"All users (considering groups) that can merge PR: {accounts_that_can_merge_pr}",
        )
        return username in accounts_that_can_merge_pr

    def request_access(self):
        raise OperationNotSupported("Not possible on Pagure")

    @indirect(PagureIssue.get_list)
    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list[Issue]:
        pass

    @indirect(PagureIssue.get)
    def get_issue(self, issue_id: int) -> Issue:
        pass

    def delete(self) -> None:
        self._call_project_api_raw("delete", method="POST")

    @indirect(PagureIssue.create)
    def create_issue(
        self,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> Issue:
        pass

    @indirect(PagurePullRequest.get_list)
    def get_pr_list(
        self,
        status: PRStatus = PRStatus.open,
        assignee=None,
        author=None,
    ) -> list[PullRequest]:
        pass

    @indirect(PagurePullRequest.get)
    def get_pr(self, pr_id: int) -> PullRequest:
        pass

    @indirect(PagurePullRequest.get_files_diff)
    def get_pr_files_diff(
        self,
        pr_id: int,
        retries: int = 0,
        wait_seconds: int = 3,
    ) -> dict:
        pass

    @if_readonly(return_function=GitProjectReadOnly.create_pr)
    @indirect(PagurePullRequest.create)
    def create_pr(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> PullRequest:
        pass

    @if_readonly(return_function=GitProjectReadOnly.fork_create)
    def fork_create(self, namespace: Optional[str] = None) -> "PagureProject":
        if namespace is not None:
            raise OperationNotSupported(
                "Pagure does not support forking to namespaces.",
            )

        request_url = self.service.get_api_url("fork")
        self.service.call_api(
            url=request_url,
            method="POST",
            data={"repo": self.repo, "namespace": self.namespace, "wait": True},
        )
        fork = self._construct_fork_project()
        logger.debug(f"Forked to {fork.full_repo_name}")
        return fork

    def _construct_fork_project(self) -> "PagureProject":
        return PagureProject(
            service=self.service,
            repo=self.repo,
            namespace=self.namespace,
            username=self._user,
            is_fork=True,
        )

    def get_fork(self, create: bool = True) -> Optional["PagureProject"]:
        if self.is_fork:
            raise OgrException("Cannot create fork from fork.")

        for fork in self.get_forks():
            fork_info = fork.get_project_info()
            if self._user == fork_info["user"]["name"]:
                return fork

        if not self.is_forked():
            if create:
                return self.fork_create()

            logger.info(
                f"Fork of {self.repo}"
                " does not exist and we were asked not to create it.",
            )
            return None
        return self._construct_fork_project()

    def exists(self) -> bool:
        response = self._call_project_api_raw()
        return response.ok

    def is_private(self) -> bool:
        host = urlparse(self.service.instance_url).hostname
        if host in [
            "git.centos.org",
            "git.stg.centos.org",
            "pagure.io",
            "src.fedoraproject.org",
            "src.stg.fedoraproject.org",
        ]:
            # private repositories are not allowed on generally used pagure instances
            return False
        raise OperationNotSupported(
            f"is_private is not implemented for {self.service.instance_url}."
            f"Please open issue in https://github.com/packit/ogr",
        )

    def is_forked(self) -> bool:
        f = self._construct_fork_project()
        return bool(f.exists() and f.parent.exists())

    def get_is_fork_from_api(self) -> bool:
        return bool(self.get_project_info()["parent"])

    @property
    def is_fork(self) -> bool:
        return self._is_fork

    @property
    def parent(self) -> Optional["PagureProject"]:
        if self.get_is_fork_from_api():
            return PagureProject(
                repo=self.repo,
                namespace=self.get_project_info()["parent"]["namespace"],
                service=self.service,
            )
        return None

    def get_git_urls(self) -> dict[str, str]:
        return_value = self._call_project_api("git", "urls")
        return return_value["urls"]

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        self.add_user_or_group(user, access_level, "user")

    def remove_user(self, user: str) -> None:
        self.add_user_or_group(user, None, "user")

    def add_group(self, group: str, access_level: AccessLevel):
        self.add_user_or_group(group, access_level, "group")

    def remove_group(self, group: str) -> None:
        self.add_user_or_group(group, None, "group")

    def add_user_or_group(
        self,
        user: str,
        access_level: Optional[AccessLevel],
        user_type: str,
    ) -> None:
        response = self._call_project_api_raw(
            "git",
            "modifyacls",
            method="POST",
            data={
                "user_type": user_type,
                "name": user,
                "acl": self.access_dict[access_level],
            },
        )

        if response.status_code == 401:
            raise PagureAPIException(
                "You are not allowed to modify ACL's",
                response_code=response.status_code,
            )

    def change_token(self, new_token: str) -> None:
        self.service.change_token(new_token)

    def get_file_content(self, path: str, ref=None) -> str:
        ref = ref or self.default_branch
        result = self._call_project_api_raw(
            "raw",
            ref,
            "f",
            path,
            add_api_endpoint_part=False,
        )

        if not result or result.reason == "NOT FOUND":
            raise FileNotFoundError(f"File '{path}' on {ref} not found")
        if result.reason != "OK":
            raise PagureAPIException(
                f"File '{path}' on {ref} not found due to {result.reason}",
            )
        return result.content.decode()

    def get_sha_from_tag(self, tag_name: str) -> str:
        tags_dict = self.get_tags_dict()
        if tag_name not in tags_dict:
            raise PagureAPIException(f"Tag '{tag_name}' not found.", response_code=404)

        return tags_dict[tag_name].commit_sha

    def commit_comment(
        self,
        commit: str,
        body: str,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> CommitComment:
        raise OperationNotSupported("Commit comments are not supported on Pagure.")

    def get_commit_comments(self, commit: str) -> list[CommitComment]:
        raise OperationNotSupported("Commit comments are not supported on Pagure.")

    @if_readonly(return_function=GitProjectReadOnly.set_commit_status)
    @indirect(PagureCommitFlag.set)
    def set_commit_status(
        self,
        commit: str,
        state: CommitStatus,
        target_url: str,
        description: str,
        context: str,
        percent: Optional[int] = None,
        uid: Optional[str] = None,
        trim: bool = False,
    ) -> "CommitFlag":
        pass

    @indirect(PagureCommitFlag.get)
    def get_commit_statuses(self, commit: str) -> list[CommitFlag]:
        pass

    def get_tags(self) -> list[GitTag]:
        response = self._call_project_api("git", "tags", params={"with_commits": True})
        return [GitTag(name=n, commit_sha=c) for n, c in response["tags"].items()]

    def get_tags_dict(self) -> dict[str, GitTag]:
        response = self._call_project_api("git", "tags", params={"with_commits": True})
        return {n: GitTag(name=n, commit_sha=c) for n, c in response["tags"].items()}

    @indirect(PagureRelease.get_list)
    def get_releases(self) -> list[Release]:
        pass

    @indirect(PagureRelease.get)
    def get_release(self, identifier=None, name=None, tag_name=None) -> PagureRelease:
        pass

    @indirect(PagureRelease.get_latest)
    def get_latest_release(self) -> Optional[PagureRelease]:
        pass

    @indirect(PagureRelease.create)
    def create_release(
        self,
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> Release:
        pass

    def get_forks(self) -> list["PagureProject"]:
        forks_url = self.service.get_api_url("projects")
        projects_response = self.service.call_api(
            url=forks_url,
            params={"fork": True, "pattern": self.repo},
        )
        return [
            PagureProject(
                repo=fork["name"],
                namespace=fork["namespace"],
                service=self.service,
                username=fork["user"]["name"],
                is_fork=True,
            )
            for fork in projects_response["projects"]
        ]

    def get_web_url(self) -> str:
        return f'{self.service.instance_url}/{self.get_project_info()["url_path"]}'

    @property
    def full_repo_name(self) -> str:
        fork = f"fork/{self._user}/" if self.is_fork else ""
        namespace = f"{self.namespace}/" if self.namespace else ""
        return f"{fork}{namespace}{self.repo}"

    def __get_files(
        self,
        path: str,
        ref: Optional[str] = None,
        recursive: bool = False,
    ) -> Iterable[str]:
        subfolders = ["."]

        while subfolders:
            path = subfolders.pop()
            split_path = []
            if path != ".":
                split_path = ["f", *path.split("/")]
            response = self._call_project_api("tree", ref, *split_path)

            for file in response["content"]:
                if file["type"] == "file":
                    yield file["path"]
                elif recursive and file["type"] == "folder":
                    subfolders.append(file["path"])

    def get_files(
        self,
        ref: Optional[str] = None,
        filter_regex: Optional[str] = None,
        recursive: bool = False,
    ) -> list[str]:
        ref = ref or self.default_branch
        paths = list(self.__get_files(".", ref, recursive))
        if filter_regex:
            paths = filter_paths(paths, filter_regex)

        return paths

    def get_sha_from_branch(self, branch: str) -> Optional[str]:
        branches = self._call_project_api(
            "git",
            "branches",
            params={"with_commits": True},
        )["branches"]

        return branches.get(branch)

    def get_contributors(self) -> set[str]:
        raise OperationNotSupported("Pagure doesn't provide list of contributors")

    def users_with_write_access(self) -> set[str]:
        return self._get_users_with_given_access(["commit", "admin", "owner"])

    def get_users_with_given_access(self, access_levels: list[AccessLevel]) -> set[str]:
        access_levels_pagure = [
            self.access_dict[access_level] for access_level in access_levels
        ]

        # for AccessLevel.maintain get the maintainer as well
        if AccessLevel.maintain in access_levels:
            access_levels_pagure.append("owner")

        return self._get_users_with_given_access(access_levels_pagure)

    def _get_users_with_given_access(self, access_levels: list[str]) -> set[str]:
        """
        Get all users (considering groups) with the access levels given by list.

        Arguments:
            access_levels: list of access levels, e.g. ['commit', 'admin']
        """
        users = self._get_user_accounts_with_access(access_levels)

        # group cannot have owner access
        group_accounts = self._get_group_accounts_with_access(
            list(set(access_levels) - {"owner"}),
        )

        users.update(
            member
            for group in group_accounts
            for member in self.service.get_group(group).members
        )

        logger.info(
            f"All users (considering groups) with given access levels: {users}",
        )
        return users

    def _get_entity_accounts_with_access(
        self,
        access_levels: list[str],
        entity_type: str,
    ) -> set[str]:
        """
        Get the entity account names (users or groups) with the access levels given by the set.

        Arguments:
            access_levels: list of access levels, e.g. ['commit', 'admin']
            entity_type: 'users' or 'groups'
        """
        if entity_type not in ("users", "groups"):
            raise OgrException(
                f"Unsupported entity type {entity_type}: only 'users' and 'groups' are allowed.",
            )
        entity_info = self.get_project_info()["access_" + entity_type]
        result = set()
        for access_level in access_levels:
            result.update(entity_info[access_level])

        return result

    def _get_user_accounts_with_access(self, access_levels: list[str]) -> set[str]:
        """
        Get the users with the access levels given by the set.
        """
        return self._get_entity_accounts_with_access(access_levels, "users")

    def _get_group_accounts_with_access(self, access_levels: list[str]) -> set[str]:
        """
        Get the groups with the access levels given by list.
        """
        return self._get_entity_accounts_with_access(access_levels, "groups")

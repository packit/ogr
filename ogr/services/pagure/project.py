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
from typing import List, Optional, Dict, Set, Iterable
from urllib.parse import urlparse

from ogr.abstract import (
    PRStatus,
    GitTag,
    CommitFlag,
    CommitComment,
    CommitStatus,
    PullRequest,
    Issue,
    IssueStatus,
    Release,
    AccessLevel,
)
from ogr.exceptions import (
    PagureAPIException,
    OgrException,
    OperationNotSupported,
)
from ogr.read_only import if_readonly, GitProjectReadOnly
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

    def __init__(
        self,
        repo: str,
        namespace: Optional[str],
        service: "ogr_pagure.PagureService",
        username: str = None,
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
        add_api_endpoint_part=True,
        method: str = None,
        params: dict = None,
        data: dict = None,
    ) -> dict:
        """
        Call project API endpoint.

        :param args: str parts of the url (e.g. "a", "b" will call "project/a/b")
        :param add_fork_part: If the projects is a fork, use "fork/username" prefix, True by default
        :param add_api_endpoint_part: Add part with API endpoint "/api/0/"
        :param method: "GET"/"POST"/...
        :param params: http(s) query parameters
        :param data: data to be sent
        :return: dict
        """
        request_url = self._get_project_url(
            *args,
            add_api_endpoint_part=add_api_endpoint_part,
            add_fork_part=add_fork_part,
        )

        return self.service.call_api(
            url=request_url, method=method, params=params, data=data
        )

    def _call_project_api_raw(
        self,
        *args,
        add_fork_part: bool = True,
        add_api_endpoint_part=True,
        method: str = None,
        params: dict = None,
        data: dict = None,
    ) -> RequestResponse:
        """
        Call project API endpoint.

        :param args: str parts of the url (e.g. "a", "b" will call "project/a/b")
        :param add_fork_part: If the projects is a fork, use "fork/username" prefix, True by default
        :param add_api_endpoint_part: Add part with API endpoint "/api/0/"
        :param method: "GET"/"POST"/...
        :param params: http(s) query parameters
        :param data: data to be sent
        :return: RequestResponse
        """
        request_url = self._get_project_url(
            *args,
            add_api_endpoint_part=add_api_endpoint_part,
            add_fork_part=add_fork_part,
        )

        return self.service.call_api_raw(
            url=request_url, method=method, params=params, data=data
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

    def get_branches(self) -> List[str]:
        return_value = self._call_project_api("git", "branches", method="GET")
        return return_value["branches"]

    @property
    def default_branch(self) -> str:
        return_value = self._call_project_api("git", "branches", method="GET")
        return return_value["default"]

    def get_description(self) -> str:
        return self.get_project_info()["description"]

    def get_owners(self) -> List[str]:
        project = self.get_project_info()
        return project["access_users"]["owner"]

    def who_can_close_issue(self) -> Set[str]:
        users: Set[str] = set()
        project = self.get_project_info()
        users.update(project["access_users"]["admin"])
        users.update(project["access_users"]["commit"])
        users.update(project["access_users"]["ticket"])
        users.update(project["access_users"]["owner"])
        return users

    def who_can_merge_pr(self) -> Set[str]:
        users: Set[str] = set()
        project = self.get_project_info()
        users.update(project["access_users"]["admin"])
        users.update(project["access_users"]["commit"])
        users.update(project["access_users"]["owner"])
        return users

    def can_merge_pr(self, username) -> bool:
        return username in self.who_can_merge_pr()

    def request_access(self):
        raise OperationNotSupported("Not possible on Pagure")

    @indirect(PagureIssue.get_list)
    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List[Issue]:
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
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Issue:
        pass

    @indirect(PagurePullRequest.get_list)
    def get_pr_list(
        self, status: PRStatus = PRStatus.open, assignee=None, author=None
    ) -> List[PullRequest]:
        pass

    @indirect(PagurePullRequest.get)
    def get_pr(self, pr_id: int) -> PullRequest:
        pass

    @if_readonly(return_function=GitProjectReadOnly.create_pr)
    @indirect(PagurePullRequest.create)
    def create_pr(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> PullRequest:
        pass

    @if_readonly(return_function=GitProjectReadOnly.fork_create)
    def fork_create(self) -> "PagureProject":
        request_url = self.service.get_api_url("fork")
        self.service.call_api(
            url=request_url,
            method="POST",
            data={"repo": self.repo, "namespace": self.namespace, "wait": True},
        )
        return self._construct_fork_project()

    def _construct_fork_project(self) -> "PagureProject":
        return PagureProject(
            service=self.service,
            repo=self.repo,
            namespace=self.namespace,
            username=self._user,
            is_fork=True,
        )

    def get_fork(self, create: bool = True) -> Optional["PagureProject"]:
        """
        Provide GitProject instance of a fork of this project.

        Returns None if this is a fork.

        :param create: create a fork if it doesn't exist
        :return: instance of GitProject or None
        """
        if self.is_fork:
            raise OgrException("Cannot create fork from fork.")

        for fork in self.get_forks():
            fork_info = fork.get_project_info()
            if self._user in fork_info["user"]["name"]:
                return fork

        if not self.is_forked():
            if create:
                return self.fork_create()
            else:
                logger.info(
                    f"Fork of {self.repo}"
                    " does not exist and we were asked not to create it."
                )
                return None
        return self._construct_fork_project()

    def exists(self) -> bool:
        response = self._call_project_api_raw()
        return response.ok

    def is_private(self) -> bool:
        """
        Is this repo private? (accessible only by users with granted access)

        :return: if yes, return True
        """
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
            f"Please open issue in https://github.com/packit/ogr"
        )

    def is_forked(self) -> bool:
        """
        Is this repo forked by the authenticated user?

        :return: if yes, return True
        """
        f = self._construct_fork_project()
        return bool(f.exists() and f.parent.exists())

    def get_is_fork_from_api(self) -> bool:
        return bool(self.get_project_info()["parent"])

    @property
    def is_fork(self) -> bool:
        return self._is_fork

    @property
    def parent(self) -> Optional["PagureProject"]:
        """
        Return parent project if this project is a fork, otherwise return None
        """
        if self.get_is_fork_from_api():
            return PagureProject(
                repo=self.repo,
                namespace=self.get_project_info()["parent"]["namespace"],
                service=self.service,
            )
        return None

    def get_git_urls(self) -> Dict[str, str]:
        return_value = self._call_project_api("git", "urls")
        return return_value["urls"]

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        """
        AccessLevel.pull => ticket
        AccessLevel.triage => ticket
        AccessLevel.push => commit
        AccessLevel.admin => commit
        AccessLevel.maintain => admin
        """
        self.add_user_or_group(user, access_level, "user")

    def add_group(self, group: str, access_level: AccessLevel):
        """
        AccessLevel.pull => ticket
        AccessLevel.triage => ticket
        AccessLevel.push => commit
        AccessLevel.admin => commit
        AccessLevel.maintain => admin
        """
        self.add_user_or_group(group, access_level, "group")

    def add_user_or_group(
        self, user: str, access_level: AccessLevel, user_type
    ) -> None:
        access_dict = {
            AccessLevel.pull: "ticket",
            AccessLevel.triage: "ticket",
            AccessLevel.push: "commit",
            AccessLevel.admin: "commit",
            AccessLevel.maintain: "admin",
        }
        response = self._call_project_api_raw(
            "git",
            "modifyacls",
            method="POST",
            data={
                "user_type": user_type,
                "name": user,
                "acl": access_dict[access_level],
            },
        )

        if response.status_code == 401:
            raise PagureAPIException("You are not allowed to modify ACL's")

    def change_token(self, new_token: str) -> None:
        """
        Change an API token.

        Only for this instance.
        """
        self.service.change_token(new_token)

    def get_file_content(self, path: str, ref=None) -> str:
        ref = ref or self.default_branch
        result = self._call_project_api_raw(
            "raw", ref, "f", path, add_api_endpoint_part=False
        )

        if not result or result.reason == "NOT FOUND":
            raise FileNotFoundError(f"File '{path}' on {ref} not found")
        return result.content.decode()

    def get_sha_from_tag(self, tag_name: str) -> str:
        tags_dict = self.get_tags_dict()
        if tag_name not in tags_dict:
            raise PagureAPIException(f"Tag '{tag_name}' not found.")

        return tags_dict[tag_name].commit_sha

    def commit_comment(
        self, commit: str, body: str, filename: str = None, row: int = None
    ) -> CommitComment:
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
        percent: int = None,
        uid: str = None,
        trim: bool = False,
    ) -> "CommitFlag":
        pass

    @indirect(PagureCommitFlag.get)
    def get_commit_statuses(self, commit: str) -> List[CommitFlag]:
        pass

    def get_tags(self) -> List[GitTag]:
        response = self._call_project_api("git", "tags", params={"with_commits": True})
        return [GitTag(name=n, commit_sha=c) for n, c in response["tags"].items()]

    def get_tags_dict(self) -> Dict[str, GitTag]:
        response = self._call_project_api("git", "tags", params={"with_commits": True})
        return {n: GitTag(name=n, commit_sha=c) for n, c in response["tags"].items()}

    def get_releases(self) -> List[Release]:
        # git tag for Pagure is shown as Release in Pagure UI
        git_tags = self.get_tags()
        return [self._release_from_git_tag(git_tag) for git_tag in git_tags]

    def get_release(self, identifier=None, name=None, tag_name=None) -> PagureRelease:
        raise OperationNotSupported

    def get_latest_release(self) -> Optional[PagureRelease]:
        raise OperationNotSupported

    def _release_from_git_tag(self, git_tag: GitTag) -> PagureRelease:
        return PagureRelease(
            tag_name=git_tag.name,
            url="",
            created_at="",
            tarball_url="",
            git_tag=git_tag,
            project=self,
        )

    def get_forks(self) -> List["PagureProject"]:
        """
        Get forks of the project.

        :return: [PagureProject]
        """
        forks_url = self.service.get_api_url("projects")
        projects_response = self.service.call_api(
            url=forks_url, params={"fork": True, "pattern": self.repo}
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
        """
        Get web URL of the project.

        :return: str
        """
        return f'{self.service.instance_url}/{self.get_project_info()["url_path"]}'

    @property
    def full_repo_name(self) -> str:
        """
        Get repo name with namespace
        e.g. 'rpms/python-docker-py'

        :return: str
        """
        fork = f"fork/{self._user}/" if self.is_fork else ""
        namespace = f"{self.namespace}/" if self.namespace else ""
        return f"{fork}{namespace}{self.repo}"

    def __get_files(
        self, path: str, ref: str = None, recursive: bool = False
    ) -> Iterable[str]:
        subfolders = ["."]

        while subfolders:
            path = subfolders.pop()
            split_path = []
            if path != ".":
                split_path = ["f"] + path.split("/")
            response = self._call_project_api("tree", ref, *split_path)

            for file in response["content"]:
                if file["type"] == "file":
                    yield file["path"]
                elif recursive and file["type"] == "folder":
                    subfolders.append(file["path"])

    def get_files(
        self, ref: str = None, filter_regex: str = None, recursive: bool = False
    ) -> List[str]:
        ref = ref or self.default_branch
        paths = list(self.__get_files(".", ref, recursive))
        if filter_regex:
            paths = filter_paths(paths, filter_regex)

        return paths

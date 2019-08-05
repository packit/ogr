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

import datetime
import logging
from typing import List, Optional, Dict, Any, Set

import requests

from ogr.abstract import PRStatus, GitTag, CommitFlag, CommitComment
from ogr.abstract import (
    PullRequest,
    PRComment,
    Issue,
    IssueStatus,
    IssueComment,
    Release,
)
from ogr.exceptions import (
    OurPagureRawRequest,
    PagureAPIException,
    OgrException,
    OperationNotSupported,
)
from ogr.factory import use_for_service
from ogr.read_only import if_readonly, GitProjectReadOnly
from ogr.parsing import parse_git_repo
from ogr.services.base import BaseGitService, BaseGitProject, BaseGitUser
from ogr.utils import RequestResponse

logger = logging.getLogger(__name__)


@use_for_service("pagure.io")
@use_for_service("src.fedoraproject.org")
class PagureService(BaseGitService):
    def __init__(
        self,
        token: str = None,
        instance_url: str = "https://src.fedoraproject.org",
        read_only: bool = False,
        insecure: bool = False,
        **_,
    ) -> None:
        super().__init__()
        self.instance_url = instance_url
        self._token = token
        self.read_only = read_only

        self.session = requests.session()

        adapter = requests.adapters.HTTPAdapter(max_retries=5)

        self.insecure = insecure
        if self.insecure:
            self.session.mount("http://", adapter)
        else:
            self.session.mount("https://", adapter)

        self.header = {"Authorization": "token " + self._token} if self._token else {}

    def __str__(self) -> str:
        return f'PagureService(read_only={self.read_only}, instance_url="{self.instance_url}")'

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, PagureService):
            return False

        return (
            self._token == o._token  # type: ignore
            and self.read_only == o.read_only  # type: ignore
            and self.instance_url == o.instance_url  # type: ignore
            and self.insecure == o.insecure  # type: ignore
            and self.header == o.header  # type: ignore
        )

    def get_project(self, **kwargs) -> "PagureProject":
        return PagureProject(service=self, **kwargs)

    def get_project_from_url(self, url: str) -> "PagureProject":
        repo_url = parse_git_repo(potential_url=url)
        project = self.get_project(
            repo=repo_url.repo,
            namespace=repo_url.namespace,
            is_fork=repo_url.is_fork,
            username=repo_url.username,
        )
        return project

    @property
    def user(self) -> "PagureUser":
        return PagureUser(service=self)

    def call_api(
        self, url: str, method: str = None, params: dict = None, data=None
    ) -> dict:
        """ Method used to call the API.
        It returns the raw JSON returned by the API or raises an exception
        if something goes wrong.
        """
        response = self.call_api_raw(url=url, method=method, params=params, data=data)

        if response.status_code == 404:
            error_msg = (
                response.json["error"]
                if response.json and "error" in response.json
                else None
            )
            raise PagureAPIException(
                f"Page `{url}` not found when calling Pagure API.",
                pagure_error=error_msg,
            )

        if not response.json:
            logger.debug(response.content)
            raise PagureAPIException("Error while decoding JSON: {0}")

        if not response.ok:
            logger.error(response.json)
            if "error" in response.json:
                error_msg = response.json["error"]
                raise PagureAPIException(
                    f"Pagure API returned an error when calling `{url}`: {error_msg}",
                    pagure_error=error_msg,
                )
            raise PagureAPIException(f"Problem with Pagure API when calling `{url}`")

        return response.json

    def call_api_raw(
        self, url: str, method: str = None, params: dict = None, data=None
    ):
        method = method or "GET"
        try:
            response = self.get_raw_request(
                method=method, url=url, params=params, data=data
            )

        except requests.exceptions.ConnectionError as er:
            logger.error(er)
            raise PagureAPIException(f"Cannot connect to url: `{url}`.", er)
        return response

    def get_raw_request(
        self, url, method="GET", params=None, data=None, header=None
    ) -> RequestResponse:

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            headers=header or self.header,
            data=data,
            verify=not self.insecure,
        )

        json_output = None
        try:
            json_output = response.json()
        except ValueError:
            logger.debug(response.text)

        return RequestResponse(
            status_code=response.status_code,
            ok=response.ok,
            content=response.content,
            json=json_output,
            reason=response.reason,
        )

    @property
    def api_url(self):
        return f"{self.instance_url}/api/0/"

    def get_api_url(self, *args, add_api_endpoint_part=True) -> str:
        """
        Get a URL from its parts.

        :param args: str parts of the url (e.g. "a", "b" will call "/a/b")
        :param add_api_endpoint_part: Add part with API endpoint "/api/0/", True by default
        :return: str
        """
        args_list: List[str] = []

        args_list += filter(lambda x: x is not None, args)

        if add_api_endpoint_part:
            return self.api_url + "/".join(args_list)
        return f"{self.instance_url}/" + "/".join(args_list)

    def get_api_version(self) -> str:
        """
        Get Pagure API version.
        :return:
        """
        request_url = self.get_api_url("version")
        return_value = self.call_api(request_url)
        return return_value["version"]

    def get_error_codes(self):
        """
        Get a dictionary of all error codes.
        :return:
        """
        request_url = self.get_api_url("error_codes")
        return_value = self.call_api(request_url)
        return return_value

    def change_token(self, token: str):
        self._token = token
        self.header = {"Authorization": "token " + self._token}


class PagureProject(BaseGitProject):
    service: PagureService

    def __init__(
        self,
        repo: str,
        namespace: Optional[str],
        service: "PagureService",
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
        return f'PagureProject(namespace="{self.namespace}", repo="{self.repo}")'

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

        return_value = self.service.call_api(
            url=request_url, method=method, params=params, data=data
        )
        return return_value

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

        return_value = self.service.call_api_raw(
            url=request_url, method=method, params=params, data=data
        )
        return return_value

    def _get_project_url(self, *args, add_fork_part=True, add_api_endpoint_part=True):
        additional_parts = []
        if self._is_fork and add_fork_part:
            additional_parts += ["fork", self._user]
        request_url = self.service.get_api_url(
            *additional_parts,
            self.namespace,
            self.repo,
            *args,
            add_api_endpoint_part=add_api_endpoint_part,
        )
        return request_url

    def get_project_info(self):
        return_value = self._call_project_api(method="GET")
        return return_value

    def get_branches(self) -> List[str]:
        return_value = self._call_project_api("git", "branches", method="GET")
        return return_value["branches"]

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

    def can_close_issue(self, username: str, issue: Issue) -> bool:
        allowed_users = self.who_can_close_issue()
        if username in allowed_users:
            return True
        if username == issue.author:
            return True

        return False

    def can_merge_pr(self, username) -> bool:
        allowed_users = self.who_can_merge_pr()
        if username in allowed_users:
            return True

        return False

    def get_issue_list(self, status: IssueStatus = IssueStatus.open) -> List[Issue]:
        payload = {"status": status.name.capitalize()}

        raw_issues = self._call_project_api("issues", params=payload)["issues"]
        issues = [self._issue_from_pagure_dict(issue_dict) for issue_dict in raw_issues]
        return issues

    def get_issue_info(self, issue_id: int) -> Issue:
        raw_issue = self._call_project_api("issue", str(issue_id))
        return self._issue_from_pagure_dict(raw_issue)

    def _get_all_issue_comments(self, issue_id: int) -> List[IssueComment]:
        raw_comments = self._call_project_api("issue", str(issue_id))["comments"]
        return [
            self._issuecomment_from_pagure_dict(raw_comment)
            for raw_comment in raw_comments
        ]

    def issue_comment(self, issue_id: int, body: str) -> IssueComment:
        payload = {"comment": body}
        self._call_project_api(
            "issue", str(issue_id), "comment", data=payload, method="POST"
        )
        return IssueComment(comment=body, author=self._username)

    def create_issue(self, title: str, body: str) -> Issue:
        payload = {"title": title, "issue_content": body}
        new_issue = self._call_project_api("new_issue", data=payload, method="POST")[
            "issue"
        ]
        return self._issue_from_pagure_dict(new_issue)

    def issue_close(self, issue_id: int) -> Issue:
        payload = {"status": "Closed"}
        self._call_project_api(
            "issue", str(issue_id), "status", data=payload, method="POST"
        )
        issue = self.get_issue_info(issue_id)
        return issue

    def get_pr_list(
        self, status: PRStatus = PRStatus.open, assignee=None, author=None
    ) -> List[PullRequest]:

        payload = {"status": status.name.capitalize()}
        if assignee is not None:
            payload["assignee"] = assignee
        if author is not None:
            payload["author"] = author

        raw_prs = self._call_project_api("pull-requests", params=payload)["requests"]
        prs = [self._pr_from_pagure_dict(pr_dict) for pr_dict in raw_prs]
        return prs

    def get_pr_info(self, pr_id: int) -> PullRequest:
        raw_pr = self._call_project_api("pull-request", str(pr_id))
        result = self._pr_from_pagure_dict(raw_pr)
        return result

    def _get_all_pr_comments(self, pr_id: int) -> List[PRComment]:
        raw_comments = self._call_project_api("pull-request", str(pr_id))["comments"]

        parsed_comments = [
            self._prcomment_from_pagure_dict(comment_dict)
            for comment_dict in raw_comments
        ]
        return parsed_comments

    @if_readonly(return_function=GitProjectReadOnly.pr_comment)
    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
    ) -> PRComment:
        payload: Dict[str, Any] = {"comment": body}
        if commit is not None:
            payload["commit"] = commit
        if filename is not None:
            payload["filename"] = filename
        if row is not None:
            payload["row"] = row

        self._call_project_api(
            "pull-request", str(pr_id), "comment", method="POST", data=payload
        )

        return PRComment(comment=body, author=self.service.user.get_username())

    @if_readonly(return_function=GitProjectReadOnly.pr_close)
    def pr_close(self, pr_id: int) -> PullRequest:
        return_value = self._call_project_api(
            "pull-request", str(pr_id), "close", method="POST"
        )

        if return_value["message"] != "Pull-request closed!":
            raise PagureAPIException(return_value["message"])

        return self.get_pr_info(pr_id)

    @if_readonly(return_function=GitProjectReadOnly.pr_merge)
    def pr_merge(self, pr_id: int) -> PullRequest:
        return_value = self._call_project_api(
            "pull-request", str(pr_id), "merge", method="POST"
        )

        if return_value["message"] != "Changes merged!":
            raise PagureAPIException(return_value["message"])

        return self.get_pr_info(pr_id)

    @if_readonly(return_function=GitProjectReadOnly.pr_create)
    def pr_create(
        self, title: str, body: str, target_branch: str, source_branch: str
    ) -> PullRequest:

        return_value = self._call_project_api(
            "pull-request",
            "new",
            method="POST",
            data={
                "title": title,
                "branch_to": target_branch,
                "branch_from": source_branch,
                "initial_comment": body,
            },
        )

        pr_object = self._pr_from_pagure_dict(return_value)
        return pr_object

    def update_pr_info(self, pr_id: int, title: str, description: str):
        """
        Update pull-request information.

        :param pr_id: int The ID of the pull request
        :param title: str The title of the pull request
        :param description str The description of the pull request
        :return: PullRequest
        """
        try:
            updated_pr = self._call_project_api(
                "pull-request",
                str(pr_id),
                method="POST",
                data={"title": title, "initial_comment": description},
            )
            logger.info(f"PR updated.")
            return self._pr_from_pagure_dict(updated_pr)
        except Exception as ex:
            raise PagureAPIException("there was an error while updating the PR", ex)

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

    def exists(self):
        response = self._call_project_api_raw()
        return response.ok

    def is_forked(self) -> bool:
        """
        Is this repo forked by the authenticated user?

        :return: if yes, return True
        """
        f = self._construct_fork_project()
        return bool(f.exists() and f.parent.exists())

    @property
    def is_fork(self) -> bool:
        return bool(self.get_project_info()["parent"])

    @property
    def parent(self) -> Optional["PagureProject"]:
        """
        Return parent project if this project is a fork, otherwise return None
        """
        if self.is_fork:
            return PagureProject(
                repo=self.repo,
                namespace=self.get_project_info()["parent"]["namespace"],
                service=self.service,
            )
        return None

    def get_git_urls(self) -> Dict[str, str]:
        return_value = self._call_project_api("git", "urls")
        return return_value["urls"]

    def _issue_from_pagure_dict(self, issue_dict: dict) -> Issue:
        return Issue(
            title=issue_dict["title"],
            id=issue_dict["id"],
            status=IssueStatus[issue_dict["status"].lower()],
            url=self._get_project_url("issue", str(issue_dict["id"])),
            description=issue_dict["content"],
            author=issue_dict["user"]["name"],
            created=datetime.datetime.fromtimestamp(int(issue_dict["date_created"])),
        )

    def _issuecomment_from_pagure_dict(self, comment_dict: dict) -> IssueComment:
        return IssueComment(
            comment=comment_dict["comment"],
            author=comment_dict["user"]["name"],
            created=datetime.datetime.fromtimestamp(int(comment_dict["date_created"])),
            edited=None,
        )

    def _pr_from_pagure_dict(self, pr_dict: dict) -> PullRequest:
        return PullRequest(
            title=pr_dict["title"],
            id=pr_dict["id"],
            status=PRStatus[pr_dict["status"].lower()],
            url="/".join(
                [
                    self.service.instance_url,
                    pr_dict["project"]["url_path"],
                    "pull-request",
                    str(pr_dict["id"]),
                ]
            ),
            description=pr_dict["initial_comment"],
            author=pr_dict["user"]["name"],
            source_branch=pr_dict["branch_from"],
            target_branch=pr_dict["branch"],
            created=datetime.datetime.fromtimestamp(int(pr_dict["date_created"])),
        )

    @staticmethod
    def _prcomment_from_pagure_dict(comment_dict: dict) -> PRComment:
        return PRComment(
            comment=comment_dict["comment"],
            author=comment_dict["user"]["name"],
            created=datetime.datetime.fromtimestamp(int(comment_dict["date_created"])),
            edited=datetime.datetime.fromtimestamp(int(comment_dict["edited_on"]))
            if comment_dict["edited_on"]
            else None,
        )

    @staticmethod
    def _commit_status_from_pagure_dict(
        status_dict: dict, uid: str = None
    ) -> CommitFlag:
        return CommitFlag(
            commit=status_dict["commit_hash"],
            comment=status_dict["comment"],
            state=status_dict["status"],
            context=status_dict["username"],
            url=status_dict["url"],
            uid=uid,
        )

    def change_token(self, new_token: str) -> None:
        """
        Change an API token.

        Only for this instance.
        """
        self.service.change_token(new_token)

    def get_file_content(self, path: str, ref="master") -> str:
        try:
            result = self._call_project_api_raw(
                "raw", ref, "f", path, add_api_endpoint_part=False
            )
            if not result or result.reason == "NOT FOUND":
                raise FileNotFoundError(f"File '{path}' on {ref} not found")
            return result.content.decode()
        except OurPagureRawRequest as ex:
            raise FileNotFoundError(f"Problem with getting file '{path}' on {ref}", ex)

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
    def set_commit_status(
        self,
        commit: str,
        state: str,
        target_url: str,
        description: str,
        context: str,
        percent: int = None,
        uid: str = None,
    ) -> "CommitFlag":
        data: Dict[str, Any] = {
            "username": context,
            "comment": description,
            "url": target_url,
            "status": state,
        }
        if percent:
            data["percent"] = percent
        if uid:
            data["uid"] = uid

        response = self._call_project_api("c", commit, "flag", method="POST", data=data)
        return self._commit_status_from_pagure_dict(
            response["flag"], uid=response["uid"]
        )

    def get_commit_statuses(self, commit: str) -> List[CommitFlag]:
        response = self._call_project_api("c", commit, "flag")
        return [
            self._commit_status_from_pagure_dict(flag) for flag in response["flags"]
        ]

    def get_tags(self) -> List[GitTag]:
        response = self._call_project_api("git", "tags", params={"with_commits": True})
        tags = [GitTag(name=n, commit_sha=c) for n, c in response["tags"].items()]
        return tags

    def get_tags_dict(self) -> Dict[str, GitTag]:
        response = self._call_project_api("git", "tags", params={"with_commits": True})
        tags_dict = {
            n: GitTag(name=n, commit_sha=c) for n, c in response["tags"].items()
        }
        return tags_dict

    def get_releases(self) -> List[Release]:
        # git tag for Pagure is shown as Release in Pagure UI
        git_tags = self.get_tags()
        return [self._release_from_git_tag(git_tag) for git_tag in git_tags]

    @staticmethod
    def _release_from_git_tag(git_tag: GitTag) -> Release:
        return Release(
            title=git_tag.name,
            body="",
            tag_name=git_tag.name,
            url="",
            created_at="",
            tarball_url="",
            git_tag=git_tag,
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
        fork_objects = [
            PagureProject(
                repo=fork["name"],
                namespace=fork["namespace"],
                service=self.service,
                username=fork["user"]["name"],
                is_fork=True,
            )
            for fork in projects_response["projects"]
        ]
        return fork_objects


class PagureUser(BaseGitUser):
    service: PagureService

    def __init__(self, service: PagureService) -> None:
        super().__init__(service=service)

    def __str__(self) -> str:
        return f'PagureUser(username="{self.get_username()}")'

    def get_username(self) -> str:
        request_url = self.service.get_api_url("-", "whoami")

        return_value = self.service.call_api(url=request_url, method="POST", data={})
        return return_value["username"]

    def get_projects(self) -> List["PagureProject"]:
        user_url = self.service.get_api_url("user", self.get_username())
        raw_projects = self.service.call_api(user_url)["repos"]

        project_objects = [
            PagureProject(
                repo=project["name"],
                namespace=project["namespace"],
                service=self.service,
            )
            for project in raw_projects
        ]
        return project_objects

    def get_forks(self) -> List["PagureProject"]:
        user_url = self.service.get_api_url("user", self.get_username())
        raw_forks = self.service.call_api(user_url)["forks"]

        fork_objects = [
            PagureProject(
                repo=fork["name"],
                namespace=fork["namespace"],
                service=self.service,
                is_fork=True,
            )
            for fork in raw_forks
        ]
        return fork_objects

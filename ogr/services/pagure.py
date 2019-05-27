import datetime
import logging
from typing import List, Optional, Dict, Any

import requests

from ogr.abstract import PRStatus, GitTag, CommitStatus, CommitComment
from ogr.abstract import PullRequest, PRComment
from ogr.exceptions import (
    OurPagureRawRequest,
    PagureAPIException,
    OgrException,
    OperationNotSupported,
)
from ogr.mock_core import readonly, GitProjectReadOnly, PersistentObjectStorage
from ogr.services.base import BaseGitService, BaseGitProject, BaseGitUser
from ogr.utils import RequestResponse

logger = logging.getLogger(__name__)


class PagureService(BaseGitService):
    persistent_storage: Optional[PersistentObjectStorage] = None

    def __init__(
        self,
        token: str = None,
        instance_url: str = "https://src.fedoraproject.org",
        read_only: bool = False,
        persistent_storage: Optional[PersistentObjectStorage] = None,
        insecure: bool = False,
    ) -> None:
        super().__init__()
        self.instance_url = instance_url
        self._token = token
        self.read_only = read_only

        if persistent_storage:
            self.persistent_storage = persistent_storage

        self.session = requests.session()

        adapter = requests.adapters.HTTPAdapter(max_retries=5)

        self.insecure = insecure
        if self.insecure:
            self.session.mount("http://", adapter)
        else:
            self.session.mount("https://", adapter)

        if self._token:
            self.header = {"Authorization": "token " + self._token}

    def get_project(self, **kwargs) -> "PagureProject":
        return PagureProject(service=self, **kwargs)

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
            raise PagureAPIException(f"Page `{url}` not found when calling Pagure API.")

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
        self, url, method="GET", params=None, data=None
    ) -> RequestResponse:

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            headers=self.header,
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
        namespace: str,
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
        return f"namespace={self.namespace} repo={self.repo}"

    def __repr__(self) -> str:
        return f"PagureProject(namespace={self.namespace}, repo={self.repo})"

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
            additional_parts += ["fork", self.service.user.get_username()]
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

    @readonly(return_function=GitProjectReadOnly.pr_comment)
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

    @readonly(return_function=GitProjectReadOnly.pr_close)
    def pr_close(self, pr_id: int) -> PullRequest:
        return_value = self._call_project_api(
            "pull-request", str(pr_id), "close", method="POST"
        )

        if return_value["message"] != "Pull-request closed!":
            raise PagureAPIException(return_value["message"])

        return self.get_pr_info(pr_id)

    @readonly(return_function=GitProjectReadOnly.pr_merge)
    def pr_merge(self, pr_id: int) -> PullRequest:
        return_value = self._call_project_api(
            "pull-request", str(pr_id), "merge", method="POST"
        )

        if return_value["message"] != "Changes merged!":
            raise PagureAPIException(return_value["message"])

        return self.get_pr_info(pr_id)

    @readonly(return_function=GitProjectReadOnly.pr_create)
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

    @readonly(return_function=GitProjectReadOnly.fork_create)
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
    ) -> CommitStatus:
        return CommitStatus(
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

    @readonly(return_function=GitProjectReadOnly.set_commit_status)
    def set_commit_status(
        self,
        commit: str,
        state: str,
        target_url: str,
        description: str,
        context: str,
        percent: int = None,
        uid: str = None,
    ) -> "CommitStatus":
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

    def get_commit_statuses(self, commit: str) -> List[CommitStatus]:
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


class PagureUser(BaseGitUser):
    service: PagureService

    def __init__(self, service: PagureService) -> None:
        super().__init__(service=service)

    def get_username(self) -> str:
        request_url = self.service.get_api_url("-", "whoami")

        return_value = self.service.call_api(url=request_url, method="POST", data={})
        return return_value["username"]

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging
from typing import List, Optional, Union

import requests
import urllib3

from ogr.exceptions import (
    PagureAPIException,
    OgrException,
    OperationNotSupported,
    OgrNetworkError,
    GitForgeInternalError,
)
from ogr.factory import use_for_service
from ogr.parsing import parse_git_repo
from ogr.services.base import BaseGitService, GitProject
from ogr.services.pagure.project import PagureProject
from ogr.services.pagure.user import PagureUser
from ogr.utils import RequestResponse

logger = logging.getLogger(__name__)


@use_for_service("pagure")
@use_for_service("src.fedoraproject.org")
@use_for_service("src.stg.fedoraproject.org")
@use_for_service("pkgs.fedoraproject.org")
@use_for_service("pkgs.stg.fedoraproject.org")
@use_for_service("git.centos.org")
@use_for_service("git.stg.centos.org")
class PagureService(BaseGitService):
    def __init__(
        self,
        token: str = None,
        instance_url: str = "https://src.fedoraproject.org",
        read_only: bool = False,
        insecure: bool = False,
        max_retries: Union[int, urllib3.util.Retry] = 5,
        **kwargs,
    ) -> None:
        super().__init__()
        self.instance_url = instance_url
        self._token = token
        self.read_only = read_only

        self.session = requests.session()

        adapter = requests.adapters.HTTPAdapter(max_retries=max_retries)

        self.insecure = insecure
        if self.insecure:
            self.session.mount("http://", adapter)
        else:
            self.session.mount("https://", adapter)

        self.header = {"Authorization": "token " + self._token} if self._token else {}

        if kwargs:
            logger.warning(f"Ignored keyword arguments: {kwargs}")

    def __str__(self) -> str:
        token_str = (
            f", token='{self._token[:1]}***{self._token[-1:]}'" if self._token else ""
        )
        insecure_str = ", insecure=True" if self.insecure else ""
        readonly_str = ", read_only=True" if self.read_only else ""

        str_result = (
            f"PagureService(instance_url='{self.instance_url}'"
            f"{token_str}"
            f"{readonly_str}"
            f"{insecure_str})"
        )
        return str_result

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

    def __hash__(self) -> int:
        return hash(str(self))

    def get_project(self, **kwargs) -> "PagureProject":
        if "username" in kwargs:
            return PagureProject(service=self, **kwargs)
        else:
            return PagureProject(
                service=self, username=self.user.get_username(), **kwargs
            )

    def get_project_from_url(self, url: str) -> "PagureProject":
        repo_url = parse_git_repo(potential_url=url)
        if not repo_url:
            raise OgrException(f"Cannot parse project url: '{url}'")

        if not repo_url.is_fork:
            repo_url.username = None

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
        """
        Call API endpoint.

        Args:
            url: URL to be called.
            method: Method of the HTTP request, e.g. `"GET"`, `"POST"`, etc.
            params: HTTP(S) query parameters in form of a dictionary.
            data: Data to be sent in form of a dictionary.

        Returns:
            Dictionary representing response.

        Raises:
            PagureAPIException, if error occurs.
        """
        response = self.call_api_raw(url=url, method=method, params=params, data=data)

        if response.status_code == 404:
            error_msg = (
                response.json_content["error"]
                if response.json_content and "error" in response.json_content
                else None
            )
            raise PagureAPIException(
                f"Page '{url}' not found when calling Pagure API.",
                pagure_error=error_msg,
                response_code=response.status_code,
            )

        if not response.json_content:
            logger.debug(response.content)
            raise PagureAPIException(
                "Error while decoding JSON: {0}", response_code=response.status_code
            )

        if not response.ok:
            logger.error(response.json_content)
            if "error" in response.json_content:
                error_msg = response.json_content["error"]
                error_msg_ext = response.json_content.get("errors", "")
                msg = f"Pagure API returned an error when calling '{url}': {error_msg}"
                if error_msg_ext:
                    msg += f" - {error_msg_ext}"
                raise PagureAPIException(
                    msg,
                    pagure_error=error_msg,
                    pagure_response=response.json_content,
                    response_code=response.status_code,
                )
            raise PagureAPIException(
                f"Problem with Pagure API when calling '{url}'",
                response_code=response.status_code,
            )

        return response.json_content

    def call_api_raw(
        self, url: str, method: str = None, params: dict = None, data=None
    ):
        """
        Call API endpoint and returns raw response.

        Args:
            url: URL to be called.
            method: Method of the HTTP request, e.g. `"GET"`, `"POST"`, etc.
            params: HTTP(S) query parameters in form of a dictionary.
            data: Data to be sent in form of a dictionary.

        Returns:
            `RequestResponse` object that represents the response from the API
            endpoint.
        """

        method = method or "GET"
        try:
            response = self.get_raw_request(
                method=method, url=url, params=params, data=data
            )

        except requests.exceptions.ConnectionError as er:
            logger.error(er)
            raise OgrNetworkError(f"Cannot connect to url: '{url}'.") from er

        if response.status_code >= 500:
            raise GitForgeInternalError(
                f"Pagure API returned {response.status_code} status for `{url}`"
                f" with reason: `{response.reason}`"
            )

        return response

    def get_raw_request(
        self, url, method="GET", params=None, data=None, header=None
    ) -> RequestResponse:
        """
        Call API endpoint and wrap the response in `RequestResponse` type.

        Args:
            url: URL to be called.
            method: Method of the HTTP request, e.g. `"GET"`, `"POST"`, etc.

                Defaults to `"GET"`.
            params: HTTP(S) query parameters in form of a dictionary.
            data: Data to be sent in form of a dictionary.
            header: Header of the HTTP request.

        Returns:
            `RequestResponse` object representing the response.

        Raises:
            ValueError, if JSON cannot be retrieved.
        """

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
        """URL to the Pagure API."""
        return f"{self.instance_url}/api/0/"

    def get_api_url(self, *args, add_api_endpoint_part: bool = True) -> str:
        """
        Get a URL from its parts.

        Args:
            *args: String parts of the URL, e.g. `"a", "b"` will call `project/a/b`
            add_api_endpoint_part: Add part with API endpoint (`/api/0/`).

                Defaults to `True`.

        Returns:
            String
        """
        args_list: List[str] = []

        args_list += filter(lambda x: x is not None, args)

        if add_api_endpoint_part:
            return self.api_url + "/".join(args_list)
        return f"{self.instance_url}/" + "/".join(args_list)

    def get_api_version(self) -> str:
        """
        Returns:
            Version of the Pagure API.
        """
        request_url = self.get_api_url("version")
        return_value = self.call_api(request_url)
        return return_value["version"]

    def get_error_codes(self):
        """
        Returns:
            Dictionary with all error codes.
        """
        request_url = self.get_api_url("error_codes")
        return_value = self.call_api(request_url)
        return return_value

    def change_token(self, token: str):
        self._token = token
        self.header = {"Authorization": "token " + self._token}

    def __handle_project_create_fail(
        self, exception: PagureAPIException, namespace: str
    ) -> None:
        if (
            exception.pagure_response
            and exception.pagure_response["errors"]["namespace"][0]
            == "Not a valid choice"
        ):
            request_url = self.get_api_url("group", namespace)

            try:
                self.call_api(request_url, data={"projects": False})
            except PagureAPIException as ex:
                raise OgrException(f"Namespace doesn't exist ({namespace}).") from ex

            raise OgrException(
                "Cannot create project in given namespace (permissions)."
            )

        raise exception

    def project_create(
        self,
        repo: str,
        namespace: Optional[str] = None,
        description: Optional[str] = None,
    ) -> PagureProject:
        request_url = self.get_api_url("new")

        parameters = {"name": repo, "description": description, "wait": True}
        if not description:
            parameters["description"] = repo
        if namespace:
            parameters["namespace"] = namespace
        else:
            namespace = self.user.get_username()

        try:
            self.call_api(request_url, "POST", data=parameters)
        except PagureAPIException as ex:
            self.__handle_project_create_fail(ex, namespace)
        return PagureProject(repo=repo, namespace=namespace, service=self)

    def list_projects(
        self,
        namespace: str = None,
        user: str = None,
        search_pattern: str = None,
        language: str = None,
    ) -> List[GitProject]:
        raise OperationNotSupported

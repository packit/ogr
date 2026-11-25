# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any, Optional

import github
import gitlab
import pyforgejo.core.api_error


class OgrException(Exception):
    """Something went wrong during our execution."""


class APIException(OgrException):
    """Generic API exception."""

    @property
    def response_code(self):
        raise NotImplementedError()


class PagureAPIException(APIException):
    """Exception related to Pagure API."""

    def __init__(
        self,
        *args: Any,
        pagure_error: Optional[str] = None,
        pagure_response: Optional[dict[str, Any]] = None,
        response_code: Optional[int] = None,
    ) -> None:
        super().__init__(*args)
        self._pagure_error = pagure_error
        self.pagure_response = pagure_response
        self._response_code = response_code

    @property
    def pagure_error(self):
        return self._pagure_error or self.__cause__

    @property
    def response_code(self):
        return self._response_code


class GithubAPIException(APIException):
    """Exception related to Github API."""

    @property
    def response_code(self):
        if self.__cause__ is None or not isinstance(
            self.__cause__,
            github.GithubException,
        ):
            return None
        return self.__cause__.status


class GitlabAPIException(APIException):
    """Exception related to Gitlab API."""

    @property
    def response_code(self):
        if self.__cause__ is None or not isinstance(self.__cause__, gitlab.GitlabError):
            return None
        return self.__cause__.response_code


class ForgejoAPIException(APIException):
    """Exception related to Forgejo API."""

    @staticmethod
    def describe(ex: pyforgejo.core.api_error.ApiError) -> str:
        """
        Short description of a pyforgejo error: the HTTP status and the
        message Forgejo sent. Unlike `str(ex)` it leaves out the response
        headers.
        """
        message = ForgejoAPIException._message_of(ex.body)
        if message is None:
            message = "" if ex.body is None else str(ex.body)
        return f"{ex.status_code} {message}".strip()

    @staticmethod
    def _message_of(body: Any) -> Optional[str]:
        if isinstance(body, dict) and isinstance(body.get("message"), str):
            return body["message"]
        if isinstance(body, str) and body:
            return body
        return None

    @property
    def response_code(self):
        if self.__cause__ is None or not isinstance(
            self.__cause__,
            pyforgejo.core.api_error.ApiError,
        ):
            return None
        return self.__cause__.status_code

    @property
    def forgejo_message(self) -> Optional[str]:
        """Error message from Forgejo's response, if there is one."""
        if self.__cause__ is None or not isinstance(
            self.__cause__,
            pyforgejo.core.api_error.ApiError,
        ):
            return None
        return self._message_of(self.__cause__.body)


class OperationNotSupported(OgrException):
    """Raise when the operation is not supported by the backend."""


class IssueTrackerDisabled(OperationNotSupported):
    """Issue tracker on the project is not enabled."""


class OgrNetworkError(OgrException):
    """Exception raised when an unexpected network error occurs."""


class GitForgeInternalError(OgrNetworkError):
    """Exception raised when git forge returns internal failure."""


class GithubAppNotInstalledError(OgrException):
    """Exception raised when GitHub App is not installed."""

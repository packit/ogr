# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional, Dict, Any

import github
import gitlab

from ogr.deprecation import deprecate_and_set_removal


class OgrException(Exception):
    """Something went wrong during our execution."""

    pass


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
        pagure_response: Optional[Dict[str, Any]] = None,
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

    @property  # type: ignore
    @deprecate_and_set_removal(
        since="0.30.0",
        remove_in="0.35.0 (or 1.0.0 if it comes sooner)",
        message="Use __cause__",
    )
    def github_error(self):
        return self.__cause__

    @property
    def response_code(self):
        if self.__cause__ is None or not isinstance(
            self.__cause__, github.GithubException
        ):
            return None
        return self.__cause__.status


class GitlabAPIException(APIException):
    """Exception related to Gitlab API."""

    @property  # type: ignore
    @deprecate_and_set_removal(
        since="0.30.0",
        remove_in="0.35.0 (or 1.0.0 if it comes sooner)",
        message="Use __cause__",
    )
    def gitlab_error(self):
        return self.__cause__

    @property
    def response_code(self):
        if self.__cause__ is None or not isinstance(self.__cause__, gitlab.GitlabError):
            return None
        return self.__cause__.response_code


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

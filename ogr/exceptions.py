# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional, Dict, Any

from ogr.deprecation import deprecate_and_set_removal


class OgrException(Exception):
    """Something went wrong during our execution."""

    pass


class PagureAPIException(OgrException):
    """Exception related to Pagure API."""

    def __init__(
        self,
        *args: Any,
        pagure_error: Optional[str] = None,
        pagure_response: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(*args)
        self._pagure_error = pagure_error
        self.pagure_response = pagure_response

    @property
    def pagure_error(self):
        return self._pagure_error or self.__cause__


class GithubAPIException(OgrException):
    """Exception related to Github API."""

    @property  # type: ignore
    @deprecate_and_set_removal(
        since="0.30.0",
        remove_in="0.35.0 (or 1.0.0 if it comes sooner)",
        message="Use __cause__",
    )
    def github_error(self):
        return self.__cause__


class GitlabAPIException(OgrException):
    """Exception related to Gitlab API."""

    @property  # type: ignore
    @deprecate_and_set_removal(
        since="0.30.0",
        remove_in="0.35.0 (or 1.0.0 if it comes sooner)",
        message="Use __cause__",
    )
    def gitlab_error(self):
        return self.__cause__


class OperationNotSupported(OgrException):
    """Raise when the operation is not supported by the backend."""


class OgrNetworkError(OgrException):
    """Exception raised when an unexpected network error occurs."""

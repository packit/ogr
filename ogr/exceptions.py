# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional, Dict, Any


class OgrException(Exception):
    """Something went wrong during our execution"""


class PagureAPIException(OgrException):
    """Exception related to Pagure API"""

    def __init__(
        self,
        *args: Any,
        pagure_error: Optional[str] = None,
        pagure_response: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(*args)
        self.pagure_error = pagure_error
        self.pagure_response = pagure_response


class GithubAPIException(OgrException):
    """Exception related to Github API"""

    def __init__(self, *args: Any, github_error: Optional[str] = None) -> None:
        super().__init__(*args)
        self.github_error = github_error


class GitlabAPIException(OgrException):
    """Exception related to Gitlab API"""

    def __init__(self, *args: Any, gitlab_error: Optional[str] = None) -> None:
        super().__init__(*args)
        self.gitlab_error = gitlab_error


class OperationNotSupported(OgrException):
    """Raise when the operation is not supported by the backend."""

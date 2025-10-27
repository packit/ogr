# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import functools
from typing import Any, Callable, Union

import github
import gitlab
import pyforgejo.core.api_error
import requests

from ogr.exceptions import (
    APIException,
    ForgejoAPIException,
    GitForgeInternalError,
    GithubAPIException,
    GitlabAPIException,
    OgrNetworkError,
)


def __check_for_internal_failure(ex: APIException):
    """
    Checks if exception is caused by internal failure from git forge.

    Args:
        ex: Wrapped exception.

    Raises:
        GitForgeInternalError, when exception was cause by an internal failure.
        APIException, exception itself when not an internal failure.
    """
    if ex.response_code is not None and ex.response_code >= 500:
        raise GitForgeInternalError from ex.__cause__
    raise ex


def __wrap_exception(
    ex: Union[
        github.GithubException,
        gitlab.GitlabError,
        pyforgejo.core.api_error.ApiError,  # type: ignore
    ],
) -> APIException:
    """
    Wraps uncaught exception in one of ogr exceptions.

    Args:
        ex: Unhandled exception from GitHub or GitLab.

    Returns:
        Wrapped `ex` in respective `APIException`.

    Raises:
        TypeError, when given unexpected type of exception.
    """
    MAPPING = {
        github.GithubException: GithubAPIException,
        gitlab.GitlabError: GitlabAPIException,
        pyforgejo.core.api_error.ApiError: ForgejoAPIException,  # type: ignore
    }

    for caught_exception, ogr_exception in MAPPING.items():
        if isinstance(ex, caught_exception):
            exc = ogr_exception(str(ex))
            exc.__cause__ = ex
            return exc

    raise TypeError("Unknown type of uncaught exception passed") from ex


def catch_common_exceptions(function: Callable) -> Any:
    """
    Decorator catching common exceptions.

    Args:
        function (Callable): Function or method to decorate.

    Raises:
        GithubAPIException, if authentication to Github failed.
        GitlabAPIException, if authentication to Gitlab failed.
        OgrNetworkError, if network problems occurred while performing a request.
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except github.BadCredentialsException as ex:
            raise GithubAPIException("Invalid Github credentials") from ex
        except gitlab.GitlabAuthenticationError as ex:
            raise GitlabAPIException("Invalid Gitlab credentials") from ex
        except requests.exceptions.ConnectionError as ex:
            raise OgrNetworkError(
                "Could not perform the request due to a network error",
            ) from ex
        except APIException as ex:
            __check_for_internal_failure(ex)
        except (
            github.GithubException,
            gitlab.GitlabError,
            pyforgejo.core.api_error.ApiError,  # type: ignore
        ) as ex:
            __check_for_internal_failure(__wrap_exception(ex))

    return wrapper


class CatchCommonErrors(type):
    """
    A metaclass wrapping methods with a common exception handler.

    This handler catches exceptions which can occur almost anywhere
    and catching them manually would be tedious and converts them
    to an appropriate ogr exception for the user. This includes
    exceptions such as:
        - authentication (from Github/Gitlab)
        - network errors
    """

    def __new__(cls, name, bases, namespace):
        for key, value in namespace.items():
            # There is an anticipated change in behaviour in Python 3.10
            # for static/class methods. From Python 3.10 they will be callable.
            # We need to achieve consistent behaviour with older versions,
            # hence the explicit handling is needed here (isinstance checking
            # works the same). Moreover, static/class method decorator must
            # be used last, especially prior to Python 3.10 since they return
            # descriptor objects and not functions.
            # See: https://bugs.python.org/issue43682
            if isinstance(value, staticmethod):
                namespace[key] = staticmethod(catch_common_exceptions(value.__func__))
            elif isinstance(value, classmethod):
                namespace[key] = classmethod(catch_common_exceptions(value.__func__))
            elif callable(namespace[key]):
                namespace[key] = catch_common_exceptions(namespace[key])
        return super().__new__(cls, name, bases, namespace)

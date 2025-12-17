# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import functools
import logging
import re
import time
from collections.abc import Iterable
from re import Match
from typing import Any, Callable, Optional, Union

from urllib3.util import Retry

try:
    # If urllib3~=2.0 is installed
    from urllib3 import BaseHTTPResponse
except ImportError:
    # If urllib3~=1.0 is installed
    from urllib3 import HTTPResponse as BaseHTTPResponse


from ogr.abstract import AnyComment, Comment

logger = logging.getLogger(__name__)


class CustomRetry(Retry):
    """
    Custom Retry class that includes 403 in RETRY_AFTER_STATUS_CODES
    so that Retry-After headers are respected for 403 errors.

    Also handles GitHub rate limit headers (X-RateLimit-Reset) when
    Retry-After is not present.
    """

    # Include 403 in the list of status codes that respect Retry-After header
    RETRY_AFTER_STATUS_CODES = frozenset([413, 429, 503, 403])

    def get_ratelimit_reset(self, response: BaseHTTPResponse) -> Optional[float]:
        """
        Get retry wait time from X-RateLimit-Reset header.

        Rate limit reset header (Unix timestamp) which is converted
        to seconds to wait, compatible with Retry-After format.

        Args:
            response: HTTP response object that may contain X-RateLimit-Reset header.

        Returns:
            Number of seconds to wait before retrying, or None if header is not present
            or cannot be parsed.
        """
        # Only check X-RateLimit-Reset for rate limit responses
        if (  # noqa: SIM102 This is more readable than a single if statement
            response.status
            in (
                403,
                429,
            )
        ):
            # urllib3 HTTPHeaderDict does a case-insensitive lookup
            # https://github.com/urllib3/urllib3/blob/83f8643ffb5b7f197457379148e2fa118ab0fcdc/src/urllib3/_collections.py#L215-L217
            if rate_limit_reset := response.headers.get(
                "X-RateLimit-Reset",
            ):
                try:
                    reset_timestamp = float(rate_limit_reset)
                except ValueError:
                    logger.error(
                        f"Could not parse X-RateLimit-Reset header '{rate_limit_reset}'",
                    )
                    return None
                else:
                    return max(0.0, reset_timestamp - time.time())
        return None

    def sleep_for_retry(self, response: BaseHTTPResponse) -> bool:
        """
        Override to handle X-RateLimit-Reset header in addition to Retry-After.

        Choose between Retry-After and X-RateLimit-Reset header.
        If both are present, choose the longer wait time.

        Args:
            response: HTTP response object that may contain Retry-After or X-RateLimit-Reset header.

        Returns:
            True if the wait time is greater than 0, False otherwise.
        """
        retry_after = self.get_retry_after(response)
        rate_limit_reset = self.get_ratelimit_reset(response)

        if not retry_after and not rate_limit_reset:
            return False

        wait_time, header = max(
            (
                (retry_after or 0, "Retry-After"),
                (rate_limit_reset or 0, "X-RateLimit-Reset"),
            ),
            key=lambda x: x[0],
        )
        logger.error(
            f"Rate limit hit (status {response.status}). "
            f"Waiting {wait_time}s until reset ({header} header)",
        )
        time.sleep(wait_time)
        return True


def filter_comments(
    comments: Union[list[AnyComment], Iterable[AnyComment]],
    filter_regex: Optional[str] = None,
    author: Optional[str] = None,
) -> Union[list[AnyComment], Iterable[AnyComment]]:
    """
    Filters comments from the given list.

    Args:
        comments: List of comments to be filtered.
        filter_regex: Regex to be used for filtering body of the
            comments.

            Defaults to `None`, which means no filtering by regex.
        author: Login of the author of the comments.

            Defaults to `None`, which means no filtering by author.

    Returns:
        List of comments that satisfy requested criteria.
    """
    if filter_regex or author:
        pattern = None
        if filter_regex:
            pattern = re.compile(filter_regex)

        comments = list(
            filter(
                lambda comment: (not pattern or bool(pattern.search(comment.body)))
                and (not author or comment.author == author),
                comments,
            ),
        )
    return comments


def search_in_comments(
    comments: Iterable[Union[str, Comment]],
    filter_regex: str,
) -> Optional[Match[str]]:
    """
    Find match in pull request description or comments.

    Args:
        comments: List of comments or bodies of comments
            to be searched through.
        filter_regex: Regex to be used for filtering with `re.search`.

    Returns:
        Match that has been found, `None` otherwise.
    """
    pattern = re.compile(filter_regex)
    for comment in comments:
        if isinstance(comment, Comment):
            comment = comment.body
        re_search = pattern.search(comment)
        if re_search:
            return re_search
    return None


class RequestResponse:
    """
    Class that holds response for Pagure requests.

    Attributes:
        status_code (int): Status code of the response.
        ok (bool): `True` if successful, `False` otherwise.
        content (bytes): Content of the response.
        json_content (Optional[Dict[Any, Any]]): JSON content of the response.
    """

    def __init__(
        self,
        status_code: int,
        ok: bool,
        content: bytes,
        json: Optional[dict[Any, Any]] = None,
        reason: Optional[str] = None,
        headers: Optional[list[tuple[Any, Any]]] = None,
        links: Optional[list[str]] = None,
        exception: Optional[dict[Any, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.ok = ok
        self.content = content
        self.json_content = json
        self.reason = reason
        self.headers = dict(headers) if headers else None
        self.links = links
        self.exception = exception

    def __str__(self) -> str:
        return (
            f"RequestResponse("
            f"status_code={self.status_code}, "
            f"ok={self.ok}, "
            f"content={self.content.decode()}, "
            f"json={self.json_content}, "
            f"reason={self.reason}, "
            f"headers={self.headers}, "
            f"links={self.links}, "
            f"exception={self.exception})"
        )

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, RequestResponse):
            return False
        return (
            self.status_code == o.status_code
            and self.ok == o.ok
            and self.content == o.content
            and self.json_content == o.json_content
            and self.reason == o.reason
            and self.headers == o.headers
            and self.links == o.links
            and self.exception == o.exception
        )

    def to_json_format(self) -> dict[str, Any]:
        """
        Returns:
            Response in a JSON format.
        """
        output = {
            "status_code": self.status_code,
            "ok": self.ok,
            "content": self.content,
        }
        if self.json_content:
            output["json"] = self.json_content
        if self.reason:
            output["reason"] = self.reason
        if self.headers:
            output["headers"] = self.headers
        if self.links:
            output["links"] = self.links
        if self.exception:
            output["exception"] = self.exception
        return output

    def json(self) -> Optional[dict[Any, Any]]:
        """
        Returns:
            JSON content of the response.
        """
        return self.json_content


def filter_paths(paths: Iterable[str], filter_regex: str) -> Iterable[str]:
    """
    Filters paths from the given list.

    Args:
        paths: List of paths to be filtered, in a form of an iterable.
        filter_regex: Regex to be used for filtering paths.

    Returns:
        List of path that satisfy regex, in a from of an iterable.
    """
    pattern = re.compile(filter_regex)
    return (path for path in paths if not pattern or bool(pattern.search(path)))


def indirect(specialized_function: Callable) -> Any:
    """
    Decorator to wrap methods on `GitProject`s that call specialized classes.

    Args:
        specialized_function: Static method of the specialized class
            that takes as first argument the `GitProject` itself.

    Returns:
        Decorator that calls `specialized_function` once called.
    """

    def indirect_caller(func):
        @functools.wraps(func)
        def indirectly_called(self, *args, **kwargs):
            return specialized_function(self, *args, **kwargs)

        return indirectly_called

    return indirect_caller


def create_retry_config(max_retries: Union[int, Retry]) -> Retry:
    """
    Create a retry configuration for the given max retries.
    Apply suggestions from https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api?apiVersion=2022-11-28

    Args:
        max_retries: Maximum number of retries.

    Returns:
        Retry configuration.
    """

    if isinstance(max_retries, Retry):
        return max_retries
    return CustomRetry(
        total=int(max_retries),
        # Retry mechanism active for these HTTP methods:
        allowed_methods=["DELETE", "GET", "PATCH", "POST", "PUT"],
        # Only retry on following HTTP status codes
        status_forcelist=[500, 503, 403, 401, 429],
        # This helps when hitting rate limits or temporary server issues
        # Exponential backoff: wait 30s, 60s, 120s between retries
        backoff_factor=30,
        # Respect Retry-After header for status codes in RETRY_AFTER_STATUS_CODES
        # (413, 429, 503, 403). CustomRetry includes 403 so Retry-After will be
        # respected for 403 errors when present.
        respect_retry_after_header=True,
        raise_on_status=True,
    )

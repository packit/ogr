# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import functools
import logging
import re
from re import Match
from typing import Any, Callable, Optional, Union

from ogr.abstract import AnyComment, Comment

logger = logging.getLogger(__name__)


def filter_comments(
    comments: list[AnyComment],
    filter_regex: Optional[str] = None,
    reverse: bool = False,
    author: Optional[str] = None,
) -> list[AnyComment]:
    """
    Filters comments from the given list.

    Args:
        comments: List of comments to be filtered.
        filter_regex: Regex to be used for filtering body of the
            comments.

            Defaults to `None`, which means no filtering by regex.
        reverse: Specifies ordering of the comments.

            Defaults to `False`, which means the order is kept from the input.
        author: Login of the author of the comments.

            Defaults to `None`, which means no filtering by author.

    Returns:
        List of comments that satisfy requested criteria.
    """
    if reverse:
        comments.reverse()

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
    comments: list[Union[str, Comment]],
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


def filter_paths(paths: list[str], filter_regex: str) -> list[str]:
    """
    Filters paths from the given list.

    Args:
        paths: List of paths to be filtered.
        filter_regex: Regex to be used for filtering paths.

    Returns:
        List of path that satisfy regex.
    """
    pattern = re.compile(filter_regex)
    return [path for path in paths if (not pattern or bool(pattern.search(path)))]


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

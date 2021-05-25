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

import functools
import logging
import re
from typing import Callable, List, Union, Match, Optional, Dict, Tuple, Any

from ogr.abstract import AnyComment, Comment

logger = logging.getLogger(__name__)


def filter_comments(
    comments: List[AnyComment],
    filter_regex: Optional[str] = None,
    reverse: bool = False,
    author: Optional[str] = None,
) -> List[AnyComment]:
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
            )
        )
    return comments


def search_in_comments(
    comments: List[Union[str, Comment]], filter_regex: str
) -> Optional[Match[str]]:
    """
    Find match in pull-request description or comments.

    :param comments: [str or PRComment]
    :param filter_regex: filter the comments' content with re.search
    :return: re.Match or None
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
    def __init__(
        self,
        status_code: int,
        ok: bool,
        content: bytes,
        json: Optional[Dict[Any, Any]] = None,
        reason: Optional[str] = None,
        headers: Optional[List[Tuple[Any, Any]]] = None,
        links: Optional[List[str]] = None,
        exception: Optional[Dict[Any, Any]] = None,
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

    def to_json_format(self) -> Dict[str, Any]:
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

    def json(self) -> Optional[Dict[Any, Any]]:
        return self.json_content


def filter_paths(paths: List[str], filter_regex: str) -> List[str]:
    """
    Find match in paths.
    :param paths:
    :param filter_regex:
    :return: [str]
    """
    pattern = re.compile(filter_regex)
    return [path for path in paths if (not pattern or bool(pattern.search(path)))]


def indirect(specialized_function: Callable) -> Any:
    """
    Decorator to wrap methods on GitProjects that call specialized classes.

    Args:
        specialized_function (Callable): Static method of the specialized class
            that takes as first argument the GitProject itself.

    Returns:
        Decorator that calls `specialized_function` once called.
    """

    def indirect_caller(func):
        @functools.wraps(func)
        def indirectly_called(self, *args, **kwargs):
            return specialized_function(self, *args, **kwargs)

        return indirectly_called

    return indirect_caller

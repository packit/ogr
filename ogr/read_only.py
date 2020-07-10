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

import datetime
import functools
import logging
from typing import Callable, Any, Optional

from ogr.abstract import (
    PullRequest,
    IssueComment,
    PRComment,
    PRStatus,
    GitProject,
    CommitComment,
    CommitFlag,
    CommitStatus,
)
from ogr.constant import DEFAULT_RO_PREFIX_STRING
from ogr.deprecation import deprecate_and_set_removal


def log_output(
    text: str, default_prefix: str = DEFAULT_RO_PREFIX_STRING, namespace: str = __name__
) -> None:
    logger = logging.getLogger(namespace)
    logger.warning(f"{default_prefix} {text}")


def if_readonly(
    *,
    return_value: Optional[Any] = None,
    return_function: Optional[Callable] = None,
    log_message: str = "",
) -> Any:
    """
    Decorator to log  function and ovewrite return value of object methods
    Ignore function name as first parameter and ignore every other parameters

    :param return_value: returned Any value if given, return_function has higher prio if set
    :param return_function: return function and give there parameters also
           original caller object return_function(self, *args, **kwargs)
    :param log_message: str string to put to logger output
    :return: Any type what is expected that function or return value returns
    """

    def decorator_readonly(func):
        @functools.wraps(func)
        def readonly_func(self, *args, **kwargs):
            if not self.read_only:
                return func(self, *args, **kwargs)
            else:
                args_str = str(args)[1:-1]
                kwargs_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
                # add , in case there are also args, what has to be separated
                if args and kwargs:
                    kwargs_str = ", " + kwargs_str
                log_output(
                    f"{log_message} {self.__class__.__name__}."
                    f"{func.__name__}({args_str}{kwargs_str})"
                )
                if return_function:
                    return return_function(self, *args, **kwargs)
                else:
                    return return_value

        return readonly_func

    return decorator_readonly


class PullRequestReadOnly(PullRequest):
    def __init__(
        self,
        title: str,
        description: str,
        target_branch: str,
        source_branch: str,
        id: int,
        status: PRStatus,
        url: str,
        author: str,
        created: datetime.datetime,
    ) -> None:
        self._title = title
        self._description = description
        self._target_branch = target_branch
        self._source_branch = source_branch
        self._id = id
        self._status = PRStatus.open
        self._url = url
        self._author = author
        self._created = created

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, new_title: str) -> None:
        self._title = new_title

    @property
    def id(self) -> int:
        return self._id

    @property
    def status(self) -> PRStatus:
        return self._status

    @property
    def url(self) -> str:
        return self._url

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, new_description: str) -> None:
        self._description = new_description

    @property
    def author(self) -> str:
        return self._author

    @property
    def source_branch(self) -> str:
        return self._source_branch

    @property
    def target_branch(self) -> str:
        return self._target_branch

    @property
    def created(self) -> datetime.datetime:
        return self._created


class GitProjectReadOnly:
    id = 1
    author = "ReadOnlyAuthor"
    url = "url://ReadOnlyURL"

    @classmethod
    @deprecate_and_set_removal(
        since="0.9.0",
        remove_in="0.14.0 (or 1.0.0 if it comes sooner)",
        message="Use create_pr",
    )
    def pr_create(
        cls,
        original_object: Any,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        return GitProjectReadOnly.create_pr(
            original_object=original_object,
            title=title,
            body=body,
            target_branch=target_branch,
            source_branch=source_branch,
        )

    @classmethod
    def create_pr(
        cls,
        original_object: Any,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        return PullRequestReadOnly(
            title=title,
            description=body,
            target_branch=target_branch,
            source_branch=source_branch,
            id=cls.id,
            status=PRStatus.open,
            url=cls.url,
            author=cls.author,
            created=datetime.datetime.now(),
        )

    @classmethod
    def pr_comment(
        cls,
        original_object: Any,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
    ) -> "PRComment":
        pull_request = original_object.get_pr_info(pr_id)
        log_output(pull_request)
        return PRComment(
            parent=pull_request,
            body=body,
            author=cls.author,
            created=datetime.datetime.now(),
            edited=datetime.datetime.now(),
        )

    @classmethod
    def pr_close(cls, original_object: Any, pr_id: int) -> "PullRequest":
        pull_request = original_object.get_pr_info(pr_id)
        pull_request._status = PRStatus.closed
        return pull_request

    @classmethod
    def pr_merge(cls, original_object: Any, pr_id: int) -> "PullRequest":
        pull_request = original_object.get_pr_info(pr_id)
        pull_request._status = PRStatus.merged
        return pull_request

    @classmethod
    def issue_comment(
        cls, original_object: Any, issue_id: int, body: str
    ) -> "IssueComment":
        issue = original_object.get_issue_info(issue_id)
        log_output(issue)
        return IssueComment(
            parent=issue,
            body=body,
            author=cls.author,
            created=datetime.datetime.now(),
            edited=datetime.datetime.now(),
        )

    @classmethod
    def fork_create(cls, original_object: Any) -> "GitProject":
        return original_object

    @classmethod
    def commit_comment(
        cls, original_object: Any, commit: str, body: str
    ) -> "CommitComment":
        return CommitComment(sha=commit, comment=body, author=cls.author)

    @classmethod
    def set_commit_status(
        cls, original_object: Any, commit: str, state: CommitStatus, context: str
    ) -> "CommitFlag":
        return CommitFlag(commit=commit, state=state, context=context)

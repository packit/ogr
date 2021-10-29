# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

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


def log_output(
    text: str, default_prefix: str = DEFAULT_RO_PREFIX_STRING, namespace: str = __name__
) -> None:
    """
    Logs output.

    Args:
        text: Text message to be logged.
        default_prefix: Prefix of the log message.

            Defaults to `DEFAULT_RO_PREFIX_STRING`.
        namespace: Namespace where the message comes from.

            Defaults to `__name__`.
    """
    logger = logging.getLogger(namespace)
    logger.warning(f"{default_prefix} {text}")


def if_readonly(
    *,
    return_value: Optional[Any] = None,
    return_function: Optional[Callable] = None,
    log_message: str = "",
) -> Any:
    """
    Decorator to log function and ovewrite return value of object methods.
    Ignore function name as first parameter and ignore every other parameters.

    Args:
        return_value: Returned value if given, `return_function`
            has higher priority if set.

            Defaults to `None`.
        return_function: Returned function with applies
            arguments and original caller.

            Defaults to `None`.
        log_message: String to be put to logger output.

            Defaults to `""`.

    Returns:
        Any value that is expected to be returned from the function call or the
        specificied return value.
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
        pull_request = original_object.get_pr(pr_id)
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
        pull_request = original_object.get_pr(pr_id)
        pull_request._status = PRStatus.closed
        return pull_request

    @classmethod
    def pr_merge(cls, original_object: Any, pr_id: int) -> "PullRequest":
        pull_request = original_object.get_pr(pr_id)
        pull_request._status = PRStatus.merged
        return pull_request

    @classmethod
    def issue_comment(
        cls, original_object: Any, issue_id: int, body: str
    ) -> "IssueComment":
        issue = original_object.get_issue(issue_id)
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

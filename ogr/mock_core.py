from typing import Callable, Any, Optional
import functools
import logging
import datetime
from ogr.abstract import PullRequest, PRComment, PRStatus, GitProject
from ogr.constant import DEFAULT_RO_PREFIX_STRING


logger = logging.getLogger(__name__)


def readonly(
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

            output_str = DEFAULT_RO_PREFIX_STRING
            if not self.read_only:
                return func(self, *args, **kwargs)
            else:
                if log_message:
                    output_str += " " + log_message
                args_str = str(args)[1:-1]
                kwargs_str = ""
                for k in kwargs:
                    if isinstance(kwargs[k], str):
                        value = "'{}'".format(kwargs[k])
                    else:
                        value = kwargs[k]
                    kwargs_str += ", {}={}".format(k, value)
                if kwargs and not args:
                    kwargs_str = kwargs_str[2:]
                logger.warning(
                    f"{output_str} {self.__class__.__name__}."
                    f"{func.__name__}({args_str}{kwargs_str})"
                )
                if return_function:
                    return return_function(self, *args, **kwargs)
                else:
                    return return_value

        return readonly_func

    return decorator_readonly


class GitProjectReadOnly:
    id = 1
    author = "ReadOnlyAuthor"
    url = "url://ReadOnlyURL"

    @classmethod
    def pr_create(
        cls,
        original_object: Any,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
    ) -> "PullRequest":
        _ = original_object
        output = PullRequest(
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
        return output

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
        _ = commit
        _ = filename
        _ = row
        _ = pull_request
        output = PRComment(
            comment=body,
            author=cls.author,
            created=datetime.datetime.now(),
            edited=datetime.datetime.now(),
        )
        return output

    @classmethod
    def pr_close(cls, original_object: Any, pr_id: int) -> "PullRequest":
        pull_request = original_object.get_pr_info(pr_id)
        pull_request.status = PRStatus.closed
        return pull_request

    @classmethod
    def pr_merge(cls, original_object: Any, pr_id: int) -> "PullRequest":
        pull_request = original_object.get_pr_info(pr_id)
        pull_request.status = PRStatus.merged
        return pull_request

    @classmethod
    def fork_create(cls, original_object: Any) -> "GitProject":
        return original_object

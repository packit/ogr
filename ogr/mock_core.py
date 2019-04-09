from typing import Callable, Any, Optional
import functools
import logging
import datetime
import os
import yaml
import collections

from ogr.abstract import PullRequest, PRComment, PRStatus, GitProject
from ogr.constant import DEFAULT_RO_PREFIX_STRING


def log_output(
    text: str, default_prefix: str = DEFAULT_RO_PREFIX_STRING, namespace: str = __name__
) -> None:
    logger = logging.getLogger(namespace)
    logger.warning(f"{default_prefix} {text}")


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
        log_output(pull_request)
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


class PersistentObjectStorage:
    storage_file: str = ""
    storage_object: dict = {}
    write_mode: bool = False

    def __init__(self, storage_file: str, write_mode: Optional[bool] = None) -> None:
        self.storage_file = storage_file
        if write_mode is not None:
            self.write_mode = write_mode
        else:
            self.write_mode = not os.path.exists(self.storage_file)
        if not self.write_mode:
            self.load()

    def __del__(self):
        if self.write_mode:
            self.dump()

    def store(self, keys: list, values: list) -> None:
        current_level = self.storage_object
        for item_num in range(len(keys)):
            item = keys[item_num]
            if not isinstance(item, collections.Hashable):
                item = str(item)
            if item_num + 1 < len(keys):
                if not current_level.get(item):
                    current_level[item] = {}
            else:
                current_level[item] = values
            current_level = current_level[item]

    def read(self, keys: list) -> Any:
        current_level = self.storage_object
        for item in keys:
            if not isinstance(item, collections.Hashable):
                item = str(item)
            current_level = current_level[item]
        return current_level

    def dump(self) -> None:
        with open(self.storage_file, "w") as yaml_file:
            yaml.dump(self.storage_object, yaml_file, default_flow_style=False)

    def load(self) -> dict:
        with open(self.storage_file, "r") as yaml_file:
            output = yaml.safe_load(yaml_file)
        self.storage_object = output
        return output

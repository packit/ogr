from typing import Callable, Any, Optional, Dict, List
import functools
import logging
import datetime
import os
import yaml
import collections

from ogr.abstract import (
    PullRequest,
    PRComment,
    PRStatus,
    GitProject,
    CommitComment,
    CommitStatus,
)
from ogr.constant import DEFAULT_RO_PREFIX_STRING
from ogr.exceptions import PersistenStorageException


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

    @classmethod
    def commit_comment(
        cls, original_object: Any, commit: str, body: str
    ) -> "CommitComment":
        output = CommitComment(sha=commit, comment=body, author=cls.author)
        return output

    @classmethod
    def set_commit_status(
        cls, original_object: Any, commit: str, state: str, context: str
    ) -> "CommitStatus":
        output = CommitStatus(commit, state, context)
        return output


class PersistentObjectStorage:
    """
    Class implements reading/writing simple JSON requests to dict structure
    and return values based on keys.
    It contains methods to reads/stores data to object and load and store them to YAML file

    storage_object: dict with structured data based on keys (eg. simple JSON requests)
    storage_file: file for reading and writing data in storage_object
    """

    storage_file: str = ""
    storage_object: Dict
    is_write_mode: bool = False
    is_flushed = True

    def __init__(self, storage_file: str, is_write_mode: Optional[bool] = None) -> None:
        """
        :param storage_file: file name location where to write/read object data
        :param is_write_mode: force read/write mode, if not set (None) it tries to guess if
                           it should write or read data based on if file exists

        """
        self.storage_file = storage_file
        if is_write_mode is not None:
            self.is_write_mode = is_write_mode
        else:
            self.is_write_mode = not os.path.exists(self.storage_file)
        if self.is_write_mode:
            self.is_flushed = False
            # load existing file if exist or use empty dir for write mode
            if os.path.exists(self.storage_file):
                self.storage_object = self.load()
            else:
                self.storage_object = {}
        else:
            if not os.path.exists(self.storage_file):
                raise PersistenStorageException(
                    f"file does not exists: {self.storage_file}"
                )
            self.storage_object = self.load()

    @staticmethod
    def transform_hashable(keys: List) -> List:
        output: List = []
        for item in keys:
            if not item:
                output.append("empty")
            elif not isinstance(item, collections.Hashable):
                output.append(str(item))
            else:
                output.append(item)
        return output

    def store(self, keys: List, values: Any) -> None:
        """
        Stores data to dictionary object based on keys values it will create structure
        if structure does not exist

        It implicitly changes type to string if key is not hashable

        :param keys: items what will be used as keys for dictionary
        :param values: It could be whatever type what is used in original object handling
        :return: None
        """

        current_level = self.storage_object
        hashable_keys = self.transform_hashable(keys)
        for item_num in range(len(hashable_keys)):
            item = hashable_keys[item_num]
            if item_num + 1 < len(hashable_keys):
                if not current_level.get(item):
                    current_level[item] = {}
            else:
                # do not override if key is already there
                # manually remove the file if you want to renew this
                if current_level.get(item):
                    return
                current_level[item] = values
            current_level = current_level[item]
        self.is_flushed = False

    def __del__(self):
        try:
            # ignore id instance deletion is done on level where is not open defined
            self.dump()
        except NameError:
            pass

    def read(self, keys: List) -> Any:
        """
        Reads data from dictionary object structure based on keys.
        If keys does not exists

        It implicitly changes type to string if key is not hashable

        :param keys: key list for searching in dict
        :return: value assigged to key items
        """
        current_level = self.storage_object
        hashable_keys = self.transform_hashable(keys)
        for item in hashable_keys:
            try:
                current_level = current_level[item]
            except KeyError:
                raise PersistenStorageException(
                    f"Keys not in storage:{self.storage_file} {hashable_keys}"
                )
        return current_level

    def dump(self) -> None:
        """
        Explicitly stores content of storage_object to storage_file path

        This method is also called when object is deleted and is set write mode to True

        :return: None
        """
        if self.is_write_mode:
            if self.is_flushed:
                return None
            with open(self.storage_file, "w") as yaml_file:
                yaml.dump(self.storage_object, yaml_file, default_flow_style=False)
            self.is_flushed = True

    def load(self) -> Dict:
        """
        Explicitly loads file content of storage_file to storage_object and return as well

        :return: dict
        """
        with open(self.storage_file, "r") as yaml_file:
            output = yaml.safe_load(yaml_file)
        self.storage_object = output
        return output

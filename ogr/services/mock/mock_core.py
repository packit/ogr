import collections
import os
from typing import Dict, List, Any

import yaml

from ogr.exceptions import PersistenStorageException


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

    def __init__(self, storage_file: str, dump_after_store: bool = False) -> None:
        """
        :param storage_file: file name location where to write/read object data
        :param dump_after_store: serialize all the data into the yaml file
                   after calling store() - no need to call it explicitly

        """
        # call dump() after store() is called
        self.dump_after_store = dump_after_store
        self.storage_file = storage_file

        self.is_write_mode = not os.path.exists(self.storage_file)

        if self.is_write_mode:
            self.is_flushed = False
            self.storage_object = {}
        else:
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
                current_level.setdefault(item, [])
                current_level[item].append(values)

            current_level = current_level[item]
        self.is_flushed = False

        if self.dump_after_store:
            self.dump()

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

            if item not in current_level:
                raise PersistenStorageException(
                    f"Keys not in storage:{self.storage_file} {hashable_keys}"
                )

            current_level = current_level[item]

        if len(current_level) == 0:
            raise PersistenStorageException(
                "No responses left. Try to regenerate response files."
            )

        result = current_level[0]
        del current_level[0]
        return result

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

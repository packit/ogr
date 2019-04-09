import os
import yaml
import collections
from typing import Optional, Any


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

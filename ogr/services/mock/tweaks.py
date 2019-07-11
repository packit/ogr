from typing import Optional

from ogr.mock_core import PersistentObjectStorage
from ogr.utils import RequestResponse


def use_persistent_storage_without_overwriting(cls):
    class ClassWithPersistentStorage(cls):
        persistent_storage: Optional[PersistentObjectStorage]

        def __init__(
            self,
            *args,
            persistent_storage: Optional[PersistentObjectStorage] = None,
            **kwargs,
        ) -> None:
            if persistent_storage:
                self.persistent_storage = persistent_storage
            super().__init__(*args, **kwargs)

    ClassWithPersistentStorage.__name__ = cls.__name__
    return ClassWithPersistentStorage


def use_persistent_storage(cls):
    class ClassWithPersistentStorage(cls):
        persistent_storage: Optional[PersistentObjectStorage]

        def __init__(
            self,
            *args,
            persistent_storage: Optional[PersistentObjectStorage] = None,
            **kwargs,
        ) -> None:
            if persistent_storage:
                self.persistent_storage = persistent_storage
            super().__init__(*args, **kwargs)

        def get_raw_request(
            self, url, method="GET", params=None, data=None, header=None
        ):
            keys_internal = [method, url, params, data]
            if self.persistent_storage.is_write_mode:
                output = super().get_raw_request(
                    url, method=method, params=params, data=data, header=header
                )
                self.persistent_storage.store(
                    keys=keys_internal, values=output.to_json_format()
                )
            else:
                output_dict = self.persistent_storage.read(keys=keys_internal)
                output = RequestResponse(**output_dict)
            return output

    ClassWithPersistentStorage.__name__ = cls.__name__
    return ClassWithPersistentStorage

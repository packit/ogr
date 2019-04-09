import logging
from ogr.mock_core import PersistentObjectStorage
import ogr.services.our_pagure as libpagure_origin
from typing import Type

logger = logging.getLogger(__name__)


class PagureMockAPI(libpagure_origin.OurPagure):
    persistent_storage: PersistentObjectStorage

    def _call_api(self, url, method="GET", params=None, data=None):
        keys_internal = [method, url, params, data]
        if self.persistent_storage.write_mode:
            output = super(PagureMockAPI, self)._call_api(url, method, params, data)
            self.persistent_storage.store(keys=keys_internal, values=output)
        else:
            logger.debug(f"Persistent libpagure API: {keys_internal}")
            output = self.persistent_storage.read(keys=keys_internal)
        return output


def get_Pagure_class(
    storage_file: str, write_mode: bool
) -> Type[libpagure_origin.OurPagure]:
    """
    returns improved Pagure class, what allows read and write communication to yaml file
    new class attribute:
         persistent_storage
    new class method:
        dump_yaml
    :param storage_file: string with
    :param write_mode: bool force write mode
    :return: Pagure class
    """
    storage = PersistentObjectStorage(storage_file, write_mode=write_mode)
    PagureMockAPI.persistent_storage = storage
    PagureMockAPI.dump_yaml = storage.dump
    return PagureMockAPI

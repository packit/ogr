import logging
from ogr.mock_core import PersistentObjectStorage
from ogr.services.our_pagure import OurPagure
from typing import Type

logger = logging.getLogger(__name__)


class PagureMockAPI(OurPagure):
    persistent_storage: PersistentObjectStorage

    def _call_api(self, url, method="GET", params=None, data=None):
        keys_internal = [method, url, params, data]
        if self.persistent_storage.is_write_mode:
            output = super()._call_api(url=url, method=method, params=params, data=data)
            self.persistent_storage.store(keys=keys_internal, values=output)
        else:
            logger.debug(f"Persistent libpagure API: {keys_internal}")
            output = self.persistent_storage.read(keys=keys_internal)
        return output

    def get_raw_request(
        self,
        *url_parts,
        method="GET",
        params=None,
        data=None,
        api_url=True,
        repo_name=False,
        namespace=False,
    ):
        keys_internal = [method, "_".join(url_parts), params, data]
        if self.persistent_storage.is_write_mode:
            output = super().get_raw_request(
                *url_parts,
                method=method,
                params=params,
                data=data,
                api_url=api_url,
                repo_name=repo_name,
                namespace=namespace,
            )
            self.persistent_storage.store(keys=keys_internal, values=output)
        else:
            logger.debug(f"Persistent libpagure API: {keys_internal}")
            output = self.persistent_storage.read(keys=keys_internal)
        return output


def get_Pagure_class(persistent_storage: PersistentObjectStorage) -> Type[OurPagure]:
    """
    returns improved Pagure class, what allows read and write communication to yaml file
    new class attribute:
         persistent_storage
    new class method:
        dump_yaml
    :param persistent_storage: storage for calls
    :return: Pagure class
    """
    PagureMockAPI.persistent_storage = persistent_storage
    return PagureMockAPI

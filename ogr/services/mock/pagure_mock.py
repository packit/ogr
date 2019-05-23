import logging
from typing import Type

from ogr.mock_core import PersistentObjectStorage
from ogr.services.pagure import PagureService

logger = logging.getLogger(__name__)


class PagureMockAPI(PagureService):
    persistent_storage: PersistentObjectStorage

    def get_raw_request(self, url, method="GET", params=None, data=None):
        keys_internal = [method, "_".join(url), params, data]
        if self.persistent_storage.is_write_mode:
            output = super().get_raw_request(
                *url, method=method, params=params, data=data
            )
            self.persistent_storage.store(keys=keys_internal, values=output)
        else:
            logger.debug(f"Persistent libpagure API: {keys_internal}")
            output = self.persistent_storage.read(keys=keys_internal)
        return output


def get_Pagure_class(
    persistent_storage: PersistentObjectStorage
) -> Type[PagureService]:
    """
    returns improved PagureService class, what allows read and write communication to yaml file
    new class attribute:
         persistent_storage
    new class method:
        dump_yaml
    :param persistent_storage: storage for calls
    :return: Pagure class
    """
    PagureMockAPI.persistent_storage = persistent_storage
    return PagureMockAPI

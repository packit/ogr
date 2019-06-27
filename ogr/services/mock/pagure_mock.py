# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
from typing import Type

from ogr.mock_core import PersistentObjectStorage
from ogr.services.pagure import PagureService
from ogr.utils import RequestResponse

logger = logging.getLogger(__name__)


class PagureMockAPI(PagureService):
    persistent_storage: PersistentObjectStorage

    def get_raw_request(self, url, method="GET", params=None, data=None):
        keys_internal = [method, url, params, data]
        if self.persistent_storage.is_write_mode:
            output = super().get_raw_request(
                url, method=method, params=params, data=data
            )
            self.persistent_storage.store(
                keys=keys_internal, values=output.to_json_format()
            )
        else:
            logger.debug(f"Persistent libpagure API: {keys_internal}")
            output_dict = self.persistent_storage.read(keys=keys_internal)
            output = RequestResponse(**output_dict)
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

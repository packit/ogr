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

import github as github_origin
import logging
from ogr.mock_core import PersistentObjectStorage
from typing import Type

logger = logging.getLogger(__name__)

old__requestEncode = github_origin.MainClass.Requester._Requester__requestEncode


def new__requestEncode(self, cnx, verb, url, parameters, requestHeaders, input, encode):
    """
    replacement for  github_origin.MainClass.Requester._Requester__requestEncode method
    """
    internal_keys = [verb, url, parameters]
    if self.persistent_storage.is_write_mode:
        status, responseHeaders, output = old__requestEncode(
            self, cnx, verb, url, parameters, requestHeaders, input, encode
        )
        self.persistent_storage.store(
            keys=internal_keys, values=[status, responseHeaders, output]
        )
    else:
        logger.debug(f"Persistent github API: {internal_keys}")
        status, responseHeaders, output = self.persistent_storage.read(
            keys=internal_keys
        )
    return status, responseHeaders, output


def get_Github_class(
    persistent_storage: PersistentObjectStorage
) -> Type[github_origin.MainClass.Github]:
    """
    returns improved Github class, what allows read and write communication to yaml file
    It replace method of Reguester class to use storage
    new class attribute:
         persistent_storage
    new class method:
        dump_yaml
    :param persistent_storage: storage for calls
    :return: Github class
    """
    github_origin.MainClass.Requester.persistent_storage = persistent_storage
    github_origin.MainClass.Requester._Requester__requestEncode = new__requestEncode

    return github_origin.MainClass.Github

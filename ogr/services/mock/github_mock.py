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

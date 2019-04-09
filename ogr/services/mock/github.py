import github as github_origin
import logging
from ogr.mock_core import PersistentObjectStorage
from typing import Type

logger = logging.getLogger(__name__)

old__requestEncode = github_origin.MainClass.Requester._Requester__requestEncode


def new__requestEncode(self, cnx, verb, url, parameters, requestHeaders, input, encode):
    if self.persistent_storage.write_mode:
        status, responseHeaders, output = old__requestEncode(
            self, cnx, verb, url, parameters, requestHeaders, input, encode
        )
        self.persistent_storage.store(
            keys=[verb, url, parameters], values=[status, responseHeaders, output]
        )
    else:
        logger.debug(f"Persistent github API: {verb}, {url}, {parameters}")
        status, responseHeaders, output = self.persistent_storage.read(
            keys=[verb, url, parameters]
        )
    return status, responseHeaders, output


def get_Github_class(
    storage_file: str, write_mode: bool
) -> Type[github_origin.MainClass.Github]:
    """
    returns improved Github class, what allows read and write communication to yaml file
    It replace method of Reguester class to use storage
    new class attribute:
         persistent_storage
    new class method:
        dump_yaml
    :param storage_file: string with
    :return: Github class
    """
    storage = PersistentObjectStorage(storage_file, write_mode=write_mode)
    github_origin.MainClass.Requester.persistent_storage = storage
    github_origin.MainClass.Requester._Requester__requestEncode = new__requestEncode
    github_origin.MainClass.Github.persistent_storage = storage
    github_origin.MainClass.Github.dump_yaml = storage.dump

    return github_origin.MainClass.Github

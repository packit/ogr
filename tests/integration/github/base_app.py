# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from ogr.services.github.service import GithubService
import os
from pathlib import Path
import tempfile
import unittest

from requre.utils import get_datafile_filename
from requre.online_replacing import record_requests_for_all_methods


@record_requests_for_all_methods()
class GithubAppTests(unittest.TestCase):
    TESTING_PRIVATE_KEY = str(
        """-----BEGIN RSA PRIVATE """ + "KEY-----\n"
        "MIIBOgIBAAJBAKNjUGah6iYPf1IscsTPiqhDcpk+SxeQlrNiunjLbqOnDP3gqw1U\n"
        "NZEGtXOuGim6nNjqheFsASIWeR3zWg8GgO8CAwEAAQJBAIU24kTr2vcxR4P+TYz+\n"
        "EnVimLstORh7gQO9iYAXjZvLtfvDwy4s0G2JIEIbKIwZ1JfmeXHku8BcBbvxkn5V\n"
        "W4ECIQDn9tQY7DlsUcZk2jAFPZJrpXINtqxy7p8mvwsB6iuYoQIhALRRZ+4KEdpW\n"
        "67KslR0PoxOwpzaOz7PkHBn7OH6zuN+PAiB82Lt1IocRhr3aABkCaQ5Kg8RsHxqX\n"
        "zVi5WO+Ku0d1oQIgQA4fHmeDWg3AovM98Vnps4fwjqgCzsO829nrgs7zYK8CIFog\n"
        "uIAEI5e2Sm4P285Pq3B7k1D/1t/cUtR4imzpDheQ\n"
        "-----END RSA PRIVATE KEY-----"
    )

    def setUp(self):
        self._service = None
        self._github_app_id = os.environ.get("GITHUB_APP_ID")
        self._github_app_private_key_path = os.environ.get(
            "GITHUB_APP_PRIVATE_KEY_PATH"
        )

        self._temporary_private_key_path = None
        self._hello_world_project = None

        if not get_datafile_filename(obj=self) and (
            not self._github_app_id or not self._github_app_private_key_path
        ):
            raise EnvironmentError(
                "You are in Requre write mode, please set "
                "GITHUB_APP_ID GITHUB_APP_PRIVATE_KEY_PATH env variables"
            )

    def tearDown(self) -> None:
        if self._temporary_private_key_path is not None:
            Path(self._temporary_private_key_path).unlink()

    @property
    def service(self):
        if not self._service:
            self._service = GithubService(
                github_app_id=self.github_app_id,
                github_app_private_key_path=self.github_app_private_key_path,
            )
        return self._service

    @property
    def hello_world_project(self):
        if not self._hello_world_project:
            self._hello_world_project = self.service.get_project(
                namespace="packit", repo="hello-world"
            )
        return self._hello_world_project

    @property
    def github_app_id(self) -> str:
        return self._github_app_id or "123"

    @property
    def github_app_private_key_path(self) -> str:
        # provided actual private key path
        if self._github_app_private_key_path:
            return self._github_app_private_key_path

        # already created temporary private key
        if self._temporary_private_key_path:
            return self._temporary_private_key_path

        # create temporary private key
        _, self._temporary_private_key_path = tempfile.mkstemp()
        Path(self._temporary_private_key_path).write_text(self.TESTING_PRIVATE_KEY)
        return self._temporary_private_key_path

    @property
    def github_app_private_key(self) -> str:
        return Path(self.github_app_private_key_path).read_text()

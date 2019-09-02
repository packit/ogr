import os
import unittest
from pathlib import Path

from ogr import GithubService
from ogr.persistent_storage import PersistentObjectStorage

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class GithubTests(unittest.TestCase):
    def setUp(self):
        self.github_app_id = os.environ.get("GITHUB_APP_ID")
        self.github_app_private_key_path = os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH")
        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_github-app_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file

        if PersistentObjectStorage().is_write_mode and (
            not self.github_app_id or not self.github_app_private_key_path
        ):
            raise EnvironmentError(
                "please set GITHUB_APP_ID GITHUB_APP_PRIVATE_KEY_PATH env variables"
            )

    def tearDown(self):
        PersistentObjectStorage().dump()

    def test_private_key(self):
        service = GithubService(
            github_app_id="123", github_app_private_key="the-very-secret-key"
        )
        assert service.github_app_private_key == "the-very-secret-key"

    def test_private_key_path(self):
        service = GithubService(
            github_app_id="123",
            github_app_private_key_path=f"{PERSISTENT_DATA_PREFIX}/testing_private_key.key",
        )
        assert service.github_app_private_key == "very-secret-key\n"

    def test_get_project(self):
        github_app_private_key = (
            Path(self.github_app_private_key_path).read_text()
            if self.github_app_private_key_path
            else """-----BEGIN RSA PRIVATE """
            + """KEY-----
MIIBOgIBAAJBAKNjUGah6iYPf1IscsTPiqhDcpk+SxeQlrNiunjLbqOnDP3gqw1U
NZEGtXOuGim6nNjqheFsASIWeR3zWg8GgO8CAwEAAQJBAIU24kTr2vcxR4P+TYz+
EnVimLstORh7gQO9iYAXjZvLtfvDwy4s0G2JIEIbKIwZ1JfmeXHku8BcBbvxkn5V
W4ECIQDn9tQY7DlsUcZk2jAFPZJrpXINtqxy7p8mvwsB6iuYoQIhALRRZ+4KEdpW
67KslR0PoxOwpzaOz7PkHBn7OH6zuN+PAiB82Lt1IocRhr3aABkCaQ5Kg8RsHxqX
zVi5WO+Ku0d1oQIgQA4fHmeDWg3AovM98Vnps4fwjqgCzsO829nrgs7zYK8CIFog
uIAEI5e2Sm4P285Pq3B7k1D/1t/cUtR4imzpDheQ
-----END RSA PRIVATE KEY-----"""
        )

        self.service = GithubService(
            github_app_id=self.github_app_id or "123",
            github_app_private_key=github_app_private_key,
        )
        project = self.service.get_project(namespace="packit-service", repo="ogr")
        assert project
        assert project.github_repo

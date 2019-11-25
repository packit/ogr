import os
import tempfile
import unittest
from pathlib import Path

from ogr import GithubService
from requre.storage import PersistentObjectStorage
from requre.utils import StorageMode

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)

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


class GithubTests(unittest.TestCase):
    def setUp(self):
        self.github_app_id = os.environ.get("GITHUB_APP_ID")
        self.github_app_private_key_path = os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH")

        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_github-app_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file

        if PersistentObjectStorage().mode == StorageMode.write and (
            not self.github_app_id or not self.github_app_private_key_path
        ):
            raise EnvironmentError(
                "please set GITHUB_APP_ID GITHUB_APP_PRIVATE_KEY_PATH env variables"
            )

    def tearDown(self):
        PersistentObjectStorage().dump()

    def test_private_key(self):
        service = GithubService(
            github_app_id="123", github_app_private_key=TESTING_PRIVATE_KEY
        )
        assert service.github_app_private_key == TESTING_PRIVATE_KEY

    def test_private_key_path(self):
        with tempfile.NamedTemporaryFile() as pr_key:
            Path(pr_key.name).write_text(TESTING_PRIVATE_KEY)
            service = GithubService(
                github_app_id="123", github_app_private_key_path=pr_key.name
            )
            assert service.github_app_private_key == TESTING_PRIVATE_KEY

    def test_get_project(self):
        github_app_private_key = (
            Path(self.github_app_private_key_path).read_text()
            if self.github_app_private_key_path
            else TESTING_PRIVATE_KEY
        )

        self.service = GithubService(
            github_app_id=self.github_app_id or "123",
            github_app_private_key=github_app_private_key,
        )
        project = self.service.get_project(namespace="packit-service", repo="ogr")
        assert project
        assert project.github_repo

    def test_get_project_having_key_as_path(self):
        github_app_private_key_path = self.github_app_private_key_path
        try:
            if not self.github_app_private_key_path:
                github_app_private_key_path = tempfile.mkstemp()[1]

            self.service = GithubService(
                github_app_id=self.github_app_id or "123",
                github_app_private_key_path=github_app_private_key_path,
            )
            project = self.service.get_project(namespace="packit-service", repo="ogr")
            assert project
            assert project.github_repo
        finally:
            if not self.github_app_private_key_path:
                Path(github_app_private_key_path).unlink()

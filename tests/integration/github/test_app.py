import os
import tempfile
from pathlib import Path
import unittest
import pytest
from ogr.exceptions import OgrException

from ogr.services.github.project import GithubProject

from ogr import GithubService
from requre.utils import get_datafile_filename
from requre.online_replacing import record_requests_for_all_methods


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


@record_requests_for_all_methods()
class GithubTests(unittest.TestCase):
    def setUp(self):
        self.github_app_id = os.environ.get("GITHUB_APP_ID")
        self.github_app_private_key_path = os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH")

        if not get_datafile_filename(obj=self) and (
            not self.github_app_id or not self.github_app_private_key_path
        ):
            raise EnvironmentError(
                "You are in Requre write mode, please set "
                "GITHUB_APP_ID GITHUB_APP_PRIVATE_KEY_PATH env variables"
            )

    def test_private_key(self):
        service = GithubService(
            github_app_id="123", github_app_private_key=TESTING_PRIVATE_KEY
        )
        assert service.authentication.private_key == TESTING_PRIVATE_KEY

    def test_private_key_path(self):
        with tempfile.NamedTemporaryFile() as pr_key:
            Path(pr_key.name).write_text(TESTING_PRIVATE_KEY)
            service = GithubService(
                github_app_id="123", github_app_private_key_path=pr_key.name
            )
            assert service.authentication.private_key == TESTING_PRIVATE_KEY

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
        project = self.service.get_project(namespace="packit", repo="ogr")
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
            project = self.service.get_project(namespace="packit", repo="ogr")
            assert project
            assert project.github_repo
        finally:
            if not self.github_app_private_key_path:
                Path(github_app_private_key_path).unlink()

    def test_github_proj_no_app_creds(self):
        service = GithubService(
            github_app_id="123", github_app_private_key=TESTING_PRIVATE_KEY
        )
        project = GithubProject(repo="packit", service=service, namespace="packit")
        with pytest.raises(OgrException) as exc:
            assert project.github_instance
        mes = str(exc.value)
        assert "No installation ID provided for packit/packit" in mes
        assert "make sure that you provided correct credentials" in mes

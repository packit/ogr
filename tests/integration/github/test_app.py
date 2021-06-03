import tempfile
from pathlib import Path
import pytest

from ogr import GithubService
from ogr.services.github.project import GithubProject
from ogr.exceptions import OgrException

from tests.integration.github.base_app import GithubAppTests
from requre.online_replacing import record_requests_for_all_methods


@record_requests_for_all_methods()
class App(GithubAppTests):
    # Tests creation of the service using GitHub App credentials
    def test_private_key(self):
        service = GithubService(
            github_app_id="123", github_app_private_key=self.TESTING_PRIVATE_KEY
        )
        assert service.authentication.private_key == self.TESTING_PRIVATE_KEY

    def test_private_key_path(self):
        with tempfile.NamedTemporaryFile() as pr_key:
            Path(pr_key.name).write_text(self.TESTING_PRIVATE_KEY)
            service = GithubService(
                github_app_id="123", github_app_private_key_path=pr_key.name
            )
            assert service.authentication.private_key == self.TESTING_PRIVATE_KEY

    # Tests basic functionality using GitHub App credentials
    def test_get_project(self):
        service = GithubService(
            github_app_id=self.github_app_id,
            github_app_private_key=self.github_app_private_key,
        )
        project = service.get_project(namespace="packit", repo="ogr")
        assert project
        assert project.github_repo

    def test_get_project_having_key_as_path(self):
        service = GithubService(
            github_app_id=self.github_app_id,
            github_app_private_key_path=self.github_app_private_key_path,
        )
        project = service.get_project(namespace="packit", repo="ogr")
        assert project
        assert project.github_repo

    # Tests with invalid credentials
    def test_github_proj_no_app_creds(self):
        service = GithubService(
            github_app_id="123", github_app_private_key=self.TESTING_PRIVATE_KEY
        )
        project = GithubProject(repo="packit", service=service, namespace="packit")
        with pytest.raises(OgrException) as exc:
            assert project.github_instance
        mes = str(exc.value)
        assert "No installation ID provided for packit/packit" in mes
        assert "make sure that you provided correct credentials" in mes

import pytest
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.pagure.base import PagureTests
from ogr.exceptions import OgrException


@record_requests_for_all_methods()
class Service(PagureTests):
    def test_project_create(self):
        """
        Remove https://pagure.io/"name" before data regeneration
        in case you are not owner of repo, create your
        """
        name = "new-ogr-testing-repo-jscotka"
        project = self.service.get_project(repo=name, namespace=None)
        assert not project.exists()

        new_project = self.service.project_create(repo=name)
        assert new_project.exists()
        assert new_project.repo == name

        project = self.service.get_project(repo=name, namespace=None)
        assert project.exists()

    def test_project_create_with_description(self):
        """
        Remove https://pagure.io/"name" before data regeneration
        in case you are not owner of repo, create your
        """
        name = "new-ogr-testing-repo-with-description"
        description = "The description of the newly created project."
        project = self.service.get_project(repo=name, namespace=None)
        assert not project.exists()

        new_project = self.service.project_create(repo=name, description=description)
        assert new_project.exists()
        assert new_project.repo == name
        assert new_project.get_description() == description

        project = self.service.get_project(repo=name, namespace=None)
        assert project.exists()
        assert new_project.get_description() == description

    def test_project_create_in_the_group(self):
        """
        Remove https://pagure.io/packit-service/new-ogr-testing-repo-in-the-group
        before data regeneration, if you have rigths to remove it, in other case
        create your suffix
        """
        name = "new-ogr-testing-repo-in-the-group-jscotka"
        namespace = "packit-service"
        project = self.service.get_project(repo=name, namespace=namespace)
        assert not project.exists()

        new_project = self.service.project_create(repo=name, namespace=namespace)
        assert new_project.exists()
        assert new_project.repo == name

        project = self.service.get_project(repo=name, namespace=namespace)
        assert project.exists()

    def test_project_create_invalid_namespace(self):
        name = "new-ogr-testing-repo"
        namespace = "nonexisting"

        with pytest.raises(OgrException, match=r".*Namespace doesn't exist.*"):
            self.service.project_create(repo=name, namespace=namespace)
        project = self.service.get_project(repo=name, namespace=namespace)
        assert not project.exists()

    def test_project_create_unauthorized_namespace(self):
        name = "new-ogr-testing-repo"
        namespace = "fedora-magazine"

        with pytest.raises(
            OgrException, match=r".*Cannot create project in given namespace.*"
        ):
            self.service.project_create(repo=name, namespace=namespace)
        project = self.service.get_project(repo=name, namespace=namespace)
        assert not project.exists()

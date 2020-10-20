import pytest
from gitlab import GitlabGetError
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.gitlab.base import GitlabTests

from ogr import GitlabService


@record_requests_for_all_methods()
class Service(GitlabTests):
    def test_project_create(self):
        """
        Remove https://gitlab.com/$USERNAME/new-ogr-testing-repo before data regeneration
        """
        name_of_the_repo = "new-ogr-testing-repo"
        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        with pytest.raises(GitlabGetError):
            assert project.gitlab_repo

        new_project = self.service.project_create(name_of_the_repo)
        assert new_project.repo == name_of_the_repo
        assert new_project.gitlab_repo

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        assert project.gitlab_repo

    def test_project_create_with_description(self):
        """
        Remove the following project before data regeneration:
        https://gitlab.com/$USERNAME/new-ogr-testing-repo-with-description
        """
        name_of_the_repo = "new-ogr-testing-repo-with-description"
        description = "The description of the newly created project."

        project = self.service.get_project(
            repo=name_of_the_repo,
            namespace=self.service.user.get_username(),
        )
        with pytest.raises(GitlabGetError):
            assert project.gitlab_repo

        new_project = self.service.project_create(
            name_of_the_repo,
            description=description,
        )
        assert new_project.repo == name_of_the_repo
        assert new_project.gitlab_repo
        assert new_project.get_description() == description

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        assert project.gitlab_repo
        assert project.get_description() == description

    def test_project_create_in_the_group(self):
        """
        Remove https://gitlab.com/packit-service/new-ogr-testing-repo-in-the-group
        before data regeneration.
        """
        name_of_the_repo = "new-ogr-testing-repo-in-the-group"
        namespace_of_the_repo = "packit-service"
        project = self.service.get_project(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        with pytest.raises(GitlabGetError):
            assert project.gitlab_repo

        new_project = self.service.project_create(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        assert new_project.repo == name_of_the_repo
        assert new_project.namespace == namespace_of_the_repo
        assert new_project.gitlab_repo

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        assert project.gitlab_repo

    def test_service_without_auth(self):
        service = GitlabService()
        assert service.gitlab_instance
        assert service.get_project(namespace="gnachman", repo="iterm2").exists()

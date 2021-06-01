from github import GithubException, UnknownObjectException
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base import GithubTests


@record_requests_for_all_methods()
class Service(GithubTests):
    def test_project_create(self):
        """
        Remove https://github.com/$USERNAME/repo_created_for_test repository before regeneration

        """
        name_of_the_repo = "repo_created_for_test"
        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        with self.assertRaises(GithubException):
            project.github_repo

        new_project = self.service.project_create(name_of_the_repo)
        assert new_project.repo == name_of_the_repo
        assert new_project.github_repo

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        assert project.github_repo

    def test_project_create_with_description(self):
        """
        Remove the following project before data regeneration:
        https://github.com/$USERNAME/new-ogr-testing-repo-with-description
        """
        name_of_the_repo = "new-ogr-testing-repo-with-description"
        description = "The description of the newly created project."

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        with self.assertRaises(GithubException):
            project.github_repo

        new_project = self.service.project_create(
            name_of_the_repo,
            description=description,
        )
        assert new_project.repo == name_of_the_repo
        assert new_project.github_repo
        assert new_project.get_description() == description

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        assert project.github_repo
        assert project.get_description() == description

    def test_project_create_in_the_group(self):
        """
        Remove https://github.com/packit/repo_created_for_test_in_group
        repository before regeneration
        """
        name_of_the_repo = "repo_created_for_test_in_group"
        namespace_of_the_repo = "packit"
        project = self.service.get_project(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        with self.assertRaises(UnknownObjectException):
            project.github_repo

        new_project = self.service.project_create(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        assert new_project.repo == name_of_the_repo
        assert new_project.namespace == namespace_of_the_repo
        assert new_project.github_repo

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        assert project.github_repo

    def test_list_projects_with_user_input(self):
        user = "packit"
        projects = self.service.list_projects(user=user)
        assert len(projects) == 26
        assert {p.namespace for p in projects} == {"packit"}

    def test_list_projects_with_user_language_input(self):
        user = "packit"
        language = "python"
        projects = self.service.list_projects(user=user, language=language)
        assert len(projects) == 15
        assert {p.namespace for p in projects} == {"packit"}

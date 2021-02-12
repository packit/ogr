from requre.online_replacing import record_requests_for_all_methods

from tests.integration.pagure.base import PagureTests
from ogr.abstract import AccessLevel


@record_requests_for_all_methods()
class GenericCommands(PagureTests):
    def test_add_user(self):
        """
        Create an empty `playground-$USER` repository with no other users/groups.
        """
        project = self.service.get_project(
            repo=f"playground-{self.service.user.get_username()}",
            namespace=None,
        )
        project.add_user("lachmanfrantisek", AccessLevel.admin)

    def test_add_group(self):
        """
        Create an empty `playground-$USER` repository with no other users/groups.
        """
        project = self.service.get_project(
            repo=f"playground-{self.service.user.get_username()}",
            namespace=None,
        )
        project.add_group("packit-test-group", AccessLevel.admin)

    def test_description(self):
        description = self.ogr_project.get_description()
        assert description.startswith("Testing repository for python-ogr package")

    def test_branches(self):
        branches = self.ogr_project.get_branches()
        assert branches
        assert set(branches) == {"master", "testPR"}

    def test_get_releases(self):
        releases = self.ogr_project.get_releases()
        assert len(releases) == 0

    def test_git_urls(self):
        urls = self.ogr_project.get_git_urls()
        assert urls
        assert len(urls) == 2
        assert "git" in urls
        assert "ssh" in urls
        assert urls["git"] == "https://pagure.io/ogr-tests.git"
        assert urls["ssh"].endswith("ssh://git@pagure.io/ogr-tests.git")

    def test_username(self):
        # changed to check just lenght, because it is based who regenerated data files
        assert len(self.service.user.get_username()) > 3

    def test_get_file(self):
        file_content = self.ogr_project.get_file_content("README.md")
        assert file_content
        assert isinstance(file_content, str)
        assert "Testing repository for python-ogr" in file_content

    def test_get_files(self):
        files = self.ogr_project.get_files()
        assert files
        assert len(files) >= 1
        assert "README.md" in files

        files = self.ogr_project.get_files(ref="for-testing-get-files", recursive=True)
        assert files
        assert len(files) >= 7
        assert "a/b/c/some_header.h" in files
        assert "a/b/c" not in files

        files = self.ogr_project.get_files(
            ref="for-testing-get-files", filter_regex=".*.c", recursive=True
        )
        assert files
        assert len(files) >= 3
        assert set(("a/b/lib.c", "a/b/main.c", "a/b/some_other_lib.c")).issubset(files)

    def test_nonexisting_file(self):
        with self.assertRaises(Exception) as _:
            self.ogr_project.get_file_content(".blablabla_nonexisting_file")

    def test_parent_project(self):
        assert self.ogr_fork.parent.namespace is None
        assert self.ogr_fork.parent.repo == "ogr-tests"

    def test_commit_statuses(self):
        flags = self.ogr_project.get_commit_statuses(
            commit="d87466de81c72231906a6597758f37f28830bb71"
        )
        assert isinstance(flags, list)
        assert len(flags) == 0

    def test_get_owners(self):
        owners = self.ogr_fork.get_owners()
        assert [self.user] == owners

    def test_pr_permissions(self):
        owners = self.ogr_project.who_can_merge_pr()
        assert "lachmanfrantisek" in owners
        assert self.ogr_project.can_merge_pr("lachmanfrantisek")

    def test_get_web_url(self):
        url = self.ogr_project.get_web_url()
        assert url == "https://pagure.io/ogr-tests"

    def test_full_repo_name(self):
        assert self.ogr_project.full_repo_name == "ogr-tests"
        assert (
            self.service.get_project(namespace="mbi", repo="ansible").full_repo_name
            == "mbi/ansible"
        )

        # test forks
        assert self.ogr_fork.full_repo_name == f"fork/{self.user}/ogr-tests"
        assert (
            self.service.get_project(
                namespace="Fedora-Infra",
                repo="ansible",
                username=self.user,
                is_fork=True,
            ).full_repo_name
            == f"fork/{self.user}/Fedora-Infra/ansible"
        )

    def test_delete(self):
        project = self.service.get_project(repo="delete-project", namespace="testing")
        project.delete()

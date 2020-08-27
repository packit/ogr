from requre.online_replacing import record_requests_for_all_methods

from tests.integration.pagure.base import PagureTests
from ogr.exceptions import PagureAPIException


@record_requests_for_all_methods()
class Forks(PagureTests):
    def test_fork(self):
        assert self.ogr_fork.exists()
        assert self.ogr_fork.is_fork
        fork_description = self.ogr_fork.get_description()
        assert fork_description
        a = self.ogr_fork.parent
        assert a
        is_forked = a.is_forked()
        assert is_forked and isinstance(is_forked, bool)
        fork = a.get_fork(create=False)
        assert fork
        assert fork.is_fork
        urls = fork.get_git_urls()
        assert "{username}" not in urls["ssh"]

    def test_fork_in_str(self):
        str_representation = str(self.ogr_fork)
        assert 'username="' in str_representation
        assert "is_fork=True" in str_representation

    def test_nonexisting_fork(self):
        ogr_project_non_existing_fork = self.service.get_project(
            namespace=None,
            repo="ogr-tests",
            username="qwertzuiopasdfghjkl",
            is_fork=True,
        )
        assert not ogr_project_non_existing_fork.exists()
        with self.assertRaises(PagureAPIException) as ex:
            ogr_project_non_existing_fork.get_description()
        assert "Project not found" in ex.exception.pagure_error

    def test_fork_property(self):
        fork = self.ogr_project.get_fork()
        assert fork
        assert fork.get_description()

    def test_create_fork(self):
        """
        Remove your fork of ogr-tests https://pagure.io/fork/$USER/ogr-tests
        before regeneration data.
        But other tests needs to have already existed user fork.
        So regenerate data for other tests, remove  data file for this test
        and regenerate it again.
        """
        not_existing_fork = self.ogr_project.get_fork(create=False)
        assert not not_existing_fork
        assert not self.ogr_project.is_forked()

        old_forks = self.ogr_project.service.user.get_forks()

        self.ogr_project.fork_create()

        assert self.ogr_project.get_fork().exists()
        assert self.ogr_project.is_forked()

        new_forks = self.ogr_project.service.user.get_forks()
        assert len(old_forks) == len(new_forks) - 1

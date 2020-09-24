from requre.online_replacing import record_requests_for_all_methods

from tests.integration.gitlab.base import GitlabTests
from ogr.exceptions import OperationNotSupported


@record_requests_for_all_methods()
class Forks(GitlabTests):
    def test_get_fork(self):
        fork = self.project.get_fork()
        assert fork
        assert fork.get_description()

    def test_is_fork(self):
        assert not self.project.is_fork
        assert self.project.is_forked()
        fork = self.project.get_fork(create=False)
        assert fork
        assert fork.is_fork

    def test_create_fork(self):
        """
        Remove https://gitlab.com/$USERNAME/ogr-tests before data regeneration
        """
        try:
            not_existing_fork = self.project.get_fork(create=False)
        except OperationNotSupported:
            self.skipTest("This python-gitlab malfunctions on listing forks.")
        assert not not_existing_fork
        assert not self.project.is_forked()

        new_fork = self.project.fork_create()

        assert self.project.get_fork()
        assert self.project.is_forked()
        assert new_fork.is_fork

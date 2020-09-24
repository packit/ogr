from github import GithubException
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base import GithubTests


@record_requests_for_all_methods()
class Forks(GithubTests):
    def test_fork(self):
        assert self.ogr_fork.is_fork is True
        fork_description = self.ogr_fork.get_description()
        assert fork_description

    def test_nonexisting_fork(self):
        self.ogr_nonexisting_fork = self.service.get_project(
            repo="omfeprkfmwpefmwpefkmwpeofjwepof", is_fork=True
        )
        with self.assertRaises(GithubException) as ex:
            self.ogr_nonexisting_fork.get_description()
        s = str(ex.exception)
        assert "Not Found" in s
        assert "404" in s

    def test_get_fork(self):
        fork = self.ogr_project.get_fork()
        assert fork
        assert fork.get_description()

    def test_is_fork(self):
        assert not self.ogr_project.is_fork
        is_forked = self.ogr_project.is_forked()
        assert isinstance(is_forked, bool)
        # `is True` is here on purpose: we want to be sure that .is_forked() returns True object
        # because Tomas had his crazy ideas and wanted to return GitProject directly,
        # stop that madman
        assert is_forked is True
        fork = self.ogr_project.get_fork(create=False)
        assert fork
        assert fork.is_fork

    def test_create_fork(self):
        """
        Remove your fork https://github.com/$USERNAME/fed-to-brew
        before regenerating the response files.
        """
        not_existing_fork = self.not_forked_project.get_fork(create=False)
        assert not not_existing_fork
        assert not self.not_forked_project.is_forked()

        old_forks = self.not_forked_project.service.user.get_forks()

        forked_project = self.not_forked_project.fork_create()
        assert (
            forked_project.namespace == forked_project.github_instance.get_user().login
        )
        assert forked_project.repo == "fed-to-brew"

        assert self.not_forked_project.get_fork().get_description()
        assert self.not_forked_project.is_forked()

        new_forks = self.not_forked_project.service.user.get_forks()
        assert len(old_forks) == len(new_forks) - 1

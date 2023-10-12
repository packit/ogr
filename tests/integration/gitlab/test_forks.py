# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.online_replacing import record_requests_for_all_methods

from ogr.exceptions import OperationNotSupported
from tests.integration.gitlab.base import GitlabTests


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

    def test_create_fork_with_namespace(self):
        """
        When regenerating create a testing namespace:
        ogr-tests-‹your login on the git forge›
        """
        namespace = f"ogr-tests-{self.service.user.get_username()}"
        expected_fork = self.service.get_project(
            namespace=namespace,
            repo=self.project.repo,
        )
        assert not expected_fork.exists(), "Fork should not exist before regenerating"

        fork = self.project.fork_create(namespace=namespace)
        assert fork.exists()
        assert fork.is_fork

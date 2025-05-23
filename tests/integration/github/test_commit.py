# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base import GithubTests


@record_requests_for_all_methods()
class Commit(GithubTests):
    def test_get_branch_commit(self):
        branch_commit = self.hello_world_project.get_commit("test-for-flock")
        assert branch_commit.sha.startswith("e2282f3")

    def test_get_relative_commit(self):
        main_branch_commit = self.hello_world_project.get_commit("test-for-flock^^")
        assert main_branch_commit.sha.startswith("7c85553")
        merge_branch_commit = self.hello_world_project.get_commit("test-for-flock^^2")
        assert merge_branch_commit.sha.startswith("aa4883c")

    def test_changes(self):
        commit = self.hello_world_project.get_commit("f06fed9")
        changes = commit.changes
        assert list(changes.files) == ["LICENSE", "README.md"]

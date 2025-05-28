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

    def test_get_prs(self):
        # Commit with PR associated
        commit_with_one_pr = self.hello_world_project.get_commit("0840e2d")
        prs = list(commit_with_one_pr.get_prs())
        assert prs
        assert len(prs) == 1
        assert prs[0].id == 556
        # Commit with no PR
        commit_without_pr = self.hello_world_project.get_commit("f2c98da")
        prs = list(commit_without_pr.get_prs())
        assert not prs
        # No test data for commit with multiple PRs

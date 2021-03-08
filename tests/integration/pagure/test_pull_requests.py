from requre.online_replacing import record_requests_for_all_methods

from tests.integration.pagure.base import PagureTests
from ogr.abstract import PRStatus, CommitStatus


@record_requests_for_all_methods()
class PullRequests(PagureTests):
    def test_pr_create_from_fork(self):
        pr = self.ogr_fork.create_pr(
            title="Testing PR",
            body="Body of the testing PR.",
            target_branch="master",
            source_branch="master",
        )
        assert pr.title == "Testing PR"
        assert pr.description == "Body of the testing PR."
        assert pr.target_branch == "master"
        assert pr.source_branch == "master"
        assert pr.status == PRStatus.open

    def test_pr_create_from_parent(self):
        pr = self.ogr_project.create_pr(
            title="Testing PR 2",
            body="Body of the testing PR.",
            target_branch="master",
            source_branch="master",
            fork_username=self.user,
        )
        assert pr.title == "Testing PR 2"
        assert pr.description == "Body of the testing PR."
        assert pr.target_branch == "master"
        assert pr.source_branch == "master"
        assert pr.status == PRStatus.open

    def test_pr_list(self):
        pr_list_default = self.ogr_project.get_pr_list()
        assert isinstance(pr_list_default, list)

        pr_list = self.ogr_project.get_pr_list(status=PRStatus.all)
        assert pr_list
        assert len(pr_list) >= 2

        assert len(pr_list_default) < len(pr_list)

    def test_pr_info(self):
        pr_info = self.ogr_project.get_pr(pr_id=5)
        assert pr_info
        assert pr_info.title.startswith("Test PR")
        assert not pr_info.description
        assert pr_info.status == PRStatus.merged
        assert pr_info.url == "https://pagure.io/ogr-tests/pull-request/5"
        assert (
            pr_info.diff_url
            == "https://pagure.io/ogr-tests/pull-request/5#request_diff"
        )
        assert pr_info.head_commit == "517121273b142293807606dbd7a2e0f514b21cc8"

    def test_set_pr_flag(self):
        # https://pagure.io/ogr-tests/pull-request/6
        pr = self.ogr_project.get_pr(pr_id=6)
        response = pr.set_flag(
            username="packit/build",
            comment="A simple RPM build.",
            url="https://packit.dev",
            status=CommitStatus.success,
            uid="553fa0c52d0367d778458af022ac8a9d",
        )
        assert response["uid"] == "553fa0c52d0367d778458af022ac8a9d"

    def test_head_commit(self):
        assert (
            self.ogr_project.get_pr(4).head_commit
            == "1b491a6718ca39c249e4e15a1b9d74fb2ff9d90a"
        )
        assert (
            self.ogr_project.get_pr(5).head_commit
            == "517121273b142293807606dbd7a2e0f514b21cc8"
        )

    def test_source_project_upstream_branch(self):
        pr = self.ogr_project.get_pr(4)
        source_project = pr.source_project
        assert source_project.namespace is None
        assert source_project.repo == "ogr-tests"

    def test_source_project_upstream_fork(self):
        pr = self.ogr_project.get_pr(6)
        source_project = pr.source_project
        assert source_project.namespace is None
        assert source_project.repo == "ogr-tests"
        assert source_project.full_repo_name == "fork/mfocko/ogr-tests"

    def test_pr_patch(self):
        pr = self.ogr_project.get_pr(5)
        patch = pr.patch
        assert isinstance(patch, bytes)
        assert "\nDate: Nov 26 2019 19:01:46 +0000\n" in patch.decode()

    def test_commits_url(self):
        pr = self.ogr_project.get_pr(5)
        assert (
            pr.commits_url == "https://pagure.io/ogr-tests/pull-request/5#commit_list"
        )

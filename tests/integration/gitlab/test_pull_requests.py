# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.online_replacing import record_requests_for_all_methods

from tests.integration.gitlab.base import GitlabTests
from ogr.abstract import PRStatus, CommitStatus


@record_requests_for_all_methods()
class PullRequests(GitlabTests):
    def test_pr_list(self):
        title = "some special title"
        pr = self.create_pull_request(title=title)
        pr_list = self.project.get_pr_list()
        count = len(pr_list)
        assert count >= 1
        assert title == pr_list[0].title
        pr.close()

    def test_pr_info(self):
        pr_info = self.project.get_pr(pr_id=1)
        assert pr_info
        assert pr_info.title == "change"
        assert pr_info.description == "description of mergerequest"
        assert (
            pr_info.url
            == "https://gitlab.com/packit-service/ogr-tests/-/merge_requests/1"
        )
        assert (
            pr_info.diff_url
            == "https://gitlab.com/packit-service/ogr-tests/-/merge_requests/1/diffs"
        )

    def test_get_all_pr_commits(self):
        commits = self.project.get_pr(1).get_all_commits()
        assert commits[0] == "d490ec67dd98f69dfdc1732b98bb3189f0e0aace"
        assert commits[1] == "3c1fb11dd358254cc3f1588f173e54e98c1d4c09"
        assert len(commits) == 2

    def test_get_all_pr_comments(self):
        comments = self.project.get_pr(1)._get_all_comments()
        count = len(comments)
        assert comments[0].body == "first comment of mergerequest"
        assert comments[0].author == "lbarcziova"
        assert count >= 2

    def test_update_pr_info(self):
        pr_info = self.project.get_pr(1)
        original_description = pr_info.description

        pr_info.update_info(description="changed description")
        pr_info = self.project.get_pr(pr_id=1)
        assert pr_info.description == "changed description"

        pr_info.update_info(description=original_description)
        pr_info = self.project.get_pr(pr_id=1)
        assert pr_info.description == original_description

    def create_pull_request(
        self, title="New PR of pr-3", body="Description", dest="master", source="pr-3"
    ):
        return self.project.create_pr(title, body, dest, source)

    def test_pr_close(self):
        pr = self.create_pull_request()
        pr_for_closing = self.project.get_pr(pr_id=pr.id)
        assert pr_for_closing.status == PRStatus.open

        closed_pr = pr_for_closing.close()
        assert closed_pr.status == PRStatus.closed

    def test_pr_merge(self):
        """
        Create new PR and update pull request ID to this test before this test
        """
        pull_request_id = 71
        pr_for_merging = self.project.get_pr(pr_id=pull_request_id)
        assert pr_for_merging.status == PRStatus.open

        # WARNING: this produces different PUT calls depending on
        # the version of python-gitlab (<2.7.0 or >=2.7.0).
        # Duplicate and manually fix the URL in the requre cassette
        # in order to work around this.
        merged_pr = pr_for_merging.merge()
        assert merged_pr.status == PRStatus.merged

    def test_pr_labels(self):
        """
        Remove labels before regenerating:
        https://gitlab.com/packit-service/ogr-tests/merge_requests/1
        """
        pr = self.project.get_pr(1)
        labels = pr.labels
        assert not labels

        pr.add_label("test_lb1", "test_lb2")

        labels = self.project.get_pr(1).labels
        assert len(labels) == 2
        assert labels[0] == "test_lb1"
        assert labels[1] == "test_lb2"

    def test_get_pr_comments_author_regex(self):
        comments = self.project.get_pr(1).get_comments(
            filter_regex="test$", author="mfocko"
        )
        assert len(comments) == 1
        assert comments[0].body.startswith("author")

    def test_get_pr_comments_author(self):
        comments = self.project.get_pr(1).get_comments(author="mfocko")
        assert len(comments) >= 10
        assert comments[0].body.startswith("second")

    def test_pr_comments_updates(self):
        comments = self.project.get_pr(19).get_comments(filter_regex="to be updated")
        assert len(comments) == 1
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "see if updating works"
        assert comments[0].body == "see if updating works"
        assert comments[0].edited > before_edited

        comments[0].body = before_comment
        assert comments[0].body == before_comment

    def test_pr_status(self):
        self.project.set_commit_status(
            commit="59b1a9bab5b5198c619270646410867788685c16",
            state=CommitStatus.success,
            target_url="https://gitlab.com/packit-service/ogr-tests",
            description="not failed test",
            context="test",
        )
        pr = self.project.get_pr(pr_id=19)

        statuses = pr.get_statuses()
        assert statuses
        assert len(statuses) >= 0
        assert statuses[-1].state == CommitStatus.success

    def test_setters(self):
        pr = self.project.get_pr(pr_id=1)

        old_title = pr.title
        pr.title = "test title"
        assert pr.title != old_title
        assert pr.title == "test title"

        pr.title = old_title
        assert pr.title == old_title

        old_description = pr.description
        pr.description = "test description"
        assert pr.description != old_description
        assert pr.description == "test description"

        pr.description = old_description
        assert pr.description == old_description

    def test_head_commit(self):
        assert (
            self.project.get_pr(12).head_commit
            == "2543f1728c7e1c2b8772d0dc11dc8b1870f4db60"
        )
        assert (
            self.project.get_pr(1).head_commit
            == "d490ec67dd98f69dfdc1732b98bb3189f0e0aace"
        )
        assert (
            self.project.get_pr(19).head_commit
            == "59b1a9bab5b5198c619270646410867788685c16"
        )

    def test_source_project_upstream_branch(self):
        pr = self.project.get_pr(23)
        source_project = pr.source_project
        assert source_project.namespace == "packit-service"
        assert source_project.repo == "ogr-tests"

    def test_source_project_upstream_fork(self):
        """
        Use PR id of a merge request from fork to upstream.
        """
        pr = self.project.get_pr(54)
        source_project = pr.source_project
        assert source_project.namespace == self.service.user.get_username()
        assert source_project.repo == "ogr-tests"

    def test_source_project_fork_fork(self):
        """
        Use PR id of a merge request from your fork to the fork itself.
        """
        project = self.service.get_project(
            repo="ogr-tests", namespace=self.service.user.get_username()
        )
        pr = project.get_pr(1)
        source_project = pr.source_project
        assert source_project.namespace == self.service.user.get_username()
        assert source_project.repo == "ogr-tests"

    def test_source_project_other_fork_fork(self):
        """
        Create MR from your fork to another fork and set PR id and username of
        the other fork if necessary.
        """
        project = self.service.get_project(
            repo="ogr-tests", namespace="lachmanfrantisek"
        )
        pr = project.get_pr(5)
        source_project = pr.source_project
        assert source_project.namespace == self.service.user.get_username()
        assert source_project.repo == "ogr-tests"

    def test_source_project_renamed_fork(self):
        pr = self.project.get_pr(24)
        source_project = pr.source_project
        assert source_project.namespace == "mfocko"
        assert source_project.repo == "definitely-not-ogr-tests"

    def test_source_project_renamed_upstream(self):
        """
        1. Create MR from your fork to upstream
        2. Set MR id
        3. Rename upstream
        """
        pr = self.service.get_project(
            repo="old-ogr-tests", namespace="packit-service"
        ).get_pr(54)
        source_project = pr.source_project
        assert source_project.namespace == self.service.user.get_username()
        assert source_project.repo == "ogr-tests"

    def test_create_pr_upstream_upstream(self):
        prs_before = len(self.project.get_pr_list(status=PRStatus.open))
        pr_upstream_upstream = self.project.create_pr(
            title="test PR: upstream -> upstream",
            body="test description",
            target_branch="master",
            source_branch="test-branch1",
        )
        assert pr_upstream_upstream.title == "test PR: upstream -> upstream"
        assert pr_upstream_upstream.status == PRStatus.open

        prs_after = len(self.project.get_pr_list(status=PRStatus.open))
        self.project.get_pr(pr_upstream_upstream.id).close()
        assert prs_after == prs_before + 1

    def test_create_pr_upstream_forkusername(self):
        prs_before = len(self.project.get_pr_list(status=PRStatus.open))
        pr_upstream_forkusername = self.project.create_pr(
            title="test PR: fork:one-more-branch -> upstream",
            body="test description",
            target_branch="master",
            source_branch="one-more-branch",
            fork_username=self.project.service.user.get_username(),
        )
        assert (
            pr_upstream_forkusername.title
            == "test PR: fork:one-more-branch -> upstream"
        )
        assert pr_upstream_forkusername.status == PRStatus.open
        assert pr_upstream_forkusername.source_project == self.project.get_fork()

        prs_after = len(self.project.get_pr_list(status=PRStatus.open))
        self.project.get_pr(pr_upstream_forkusername.id).close()
        assert prs_after == prs_before + 1

    def test_create_pr_upstream_fork(self):
        prs_before = len(self.project.get_pr_list(status=PRStatus.open))
        pr_upstream_fork = self.project.get_fork().create_pr(
            title="test PR: fork -> upstream",
            body="test description",
            target_branch="master",
            source_branch="one-more-branch",
        )
        assert pr_upstream_fork.title == "test PR: fork -> upstream"
        assert pr_upstream_fork.status == PRStatus.open

        prs_after = len(self.project.get_pr_list(status=PRStatus.open))
        self.project.get_pr(pr_upstream_fork.id).close()
        assert prs_after == prs_before + 1

    def test_pr_create_fork_fork(self):
        """
        Tests creating PR from fork to the fork itself.
        """
        user = self.service.user.get_username()
        fork_project = self.service.get_project(namespace=user, repo="ogr-tests")

        pr_opened_before = len(fork_project.get_pr_list(status=PRStatus.open))
        opened_pr = fork_project.create_pr(
            title="test: fork(master) <- fork",
            body="pull request body",
            target_branch="master",
            source_branch="one-more-branch",
            fork_username=user,
        )
        pr_opened_after = len(fork_project.get_pr_list(status=PRStatus.open))

        assert opened_pr.title == "test: fork(master) <- fork"
        assert opened_pr.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

        opened_pr.close()
        assert opened_pr.status == PRStatus.closed

    def test_create_pr_fork_other_fork(self):
        username = "jscotka"
        other_fork = self.service.get_project(
            repo="ogr-tests",
            namespace=username,
        )

        prs_before = len(other_fork.get_pr_list(status=PRStatus.open))
        pr_fork_fork = self.project.get_fork().create_pr(
            title="test PR: fork -> other_fork",
            body="test description",
            target_branch="master",
            source_branch="one-more-branch",
            fork_username=username,
        )
        assert pr_fork_fork.title == "test PR: fork -> other_fork"
        assert pr_fork_fork.status == PRStatus.open

        prs_after = len(other_fork.get_pr_list(status=PRStatus.open))
        self.project.get_pr(pr_fork_fork.id).close()
        assert prs_after == prs_before + 1

    def test_commits_url(self):
        pr = self.project.get_pr(3)
        assert (
            pr.commits_url
            == "https://gitlab.com/packit-service/ogr-tests/-/merge_requests/3/commits"
        )

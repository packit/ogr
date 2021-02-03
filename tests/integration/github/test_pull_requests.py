from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base import GithubTests
from ogr.abstract import PRStatus


@record_requests_for_all_methods()
class PullRequests(GithubTests):
    def test_pr_list(self):
        pr_list = self.ogr_fork.get_pr_list()
        assert isinstance(pr_list, list)

        pr_list_all = self.ogr_project.get_pr_list(status=PRStatus.all)
        assert pr_list_all
        assert len(pr_list_all) >= 75

        pr_list_closed = self.ogr_project.get_pr_list(status=PRStatus.closed)
        assert pr_list_closed
        assert len(pr_list_closed) >= 70

        closed_pr_numbers = []
        for closed_pr in pr_list_closed:
            closed_pr_numbers.append(closed_pr.id)
        assert 93 in closed_pr_numbers

        pr_list_merged = self.ogr_project.get_pr_list(status=PRStatus.merged)
        assert pr_list_merged
        assert len(pr_list_merged) >= 1
        closed_pr_numbers = []
        for closed_pr in pr_list_merged:
            closed_pr_numbers.append(closed_pr.id)
        assert 93 not in closed_pr_numbers

        pr_list = self.ogr_project.get_pr_list()
        assert pr_list
        assert len(pr_list) >= 1

    def test_pr_info(self):
        pr_info = self.ogr_project.get_pr(1)
        assert pr_info
        assert pr_info.title == "WIP: API"
        assert pr_info.status == PRStatus.merged
        assert pr_info.author == "lachmanfrantisek"
        assert pr_info.url == "https://github.com/packit/ogr/pull/1"
        assert pr_info.diff_url == "https://github.com/packit/ogr/pull/1/files"

    def test_all_pr_commits(self):
        commits = self.ogr_project.get_pr(1).get_all_commits()
        assert len(commits) == 3
        assert commits[0] == "431f4a7c5cce24c3035b17c5131a3918ab989bd0"
        assert commits[2] == "5d6cc05d30ef0a0d69bb42bdcaad187408a070b0"

    def test_update_pr_info(self):
        pr = self.hello_world_project.get_pr(pr_id=72)
        original_title = pr.title
        original_description = pr.description

        pr.update_info(title="changed title", description="changed description")
        assert pr.title == "changed title"
        assert pr.description == "changed description"

        pr.update_info(title=original_title, description=original_description)
        assert pr.title == original_title
        assert pr.description == original_description

    def test_pr_create_upstream_upstream(self):
        """
        Tests creating PR from upstream to the upstream itself.

        Requires  packit_service:test_source to be ahead of packit_service:test_target
        at least by one commit.
        """
        gh_project = self.hello_world_project
        pr_opened_before = len(gh_project.get_pr_list(status=PRStatus.open))
        pr_upstream_upstream = gh_project.create_pr(
            title="test: upstream <- upstream",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
        )
        pr_opened_after = len(gh_project.get_pr_list(status=PRStatus.open))

        assert pr_upstream_upstream.title == "test: upstream <- upstream"
        assert pr_upstream_upstream.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

        pr_upstream_upstream.close()
        assert pr_upstream_upstream.status == PRStatus.closed

    def test_pr_create_upstream_forkusername(self):
        """
        Tests creating PR from fork to upstream, by calling create_pr on upstream
        with specified fork.

        Requires  packit_service:test_source to be ahead of packit_service:test_target
        at least by one commit.
        """

        gh_project = self.hello_world_project
        pr_opened_before = len(gh_project.get_pr_list(status=PRStatus.open))
        pr_upstream_forkusername = gh_project.create_pr(
            title="test: upstream <- fork_username:source_branch",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
            fork_username=self.hello_world_project.service.user.get_username(),
        )
        pr_opened_after = len(gh_project.get_pr_list(status=PRStatus.open))

        assert (
            pr_upstream_forkusername.title
            == "test: upstream <- fork_username:source_branch"
        )
        assert pr_upstream_forkusername.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

        pr_upstream_forkusername.close()
        assert pr_upstream_forkusername.status == PRStatus.closed

    def test_pr_create_upstream_fork(self):
        """
        Tests creating PR from fork to the upstream, by calling create_pr on fork.

        Requires  packit_service:test_source to be ahead of packit_service:test_target
        at least by one commit.
        """

        gh_project = self.hello_world_project
        pr_opened_before = len(gh_project.get_pr_list(status=PRStatus.open))
        pr_upstream_fork = gh_project.get_fork().create_pr(
            title="test: upstream <- fork",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
        )
        pr_opened_after = len(gh_project.get_pr_list(status=PRStatus.open))

        assert pr_upstream_fork.title == "test: upstream <- fork"
        assert pr_upstream_fork.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

        pr_upstream_fork.close()
        assert pr_upstream_fork.status == PRStatus.closed

    def test_pr_create_fork_other_fork(self):
        """
        Tests creating PR from one fork to another.
        """
        fork_project = self.service.get_project(namespace="mfocko", repo="hello-world")
        other_fork_project = self.service.get_project(
            namespace="lachmanfrantisek", repo="hello-world"
        )
        pr_opened_before = len(other_fork_project.get_pr_list(status=PRStatus.open))
        opened_pr = fork_project.create_pr(
            title="test: other_fork(master) <- fork",
            body="pull request body",
            target_branch="master",
            source_branch="test_source",
            fork_username="lachmanfrantisek",
        )
        pr_opened_after = len(other_fork_project.get_pr_list(status=PRStatus.open))

        assert opened_pr.title == "test: other_fork(master) <- fork"
        assert opened_pr.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

        opened_pr.close()
        assert opened_pr.status == PRStatus.closed

    def test_pr_create_fork_fork(self):
        """
        Tests creating PR from fork to the fork itself.
        """
        user = self.service.user.get_username()
        fork_project = self.service.get_project(namespace=user, repo="hello-world")

        pr_opened_before = len(fork_project.get_pr_list(status=PRStatus.open))
        opened_pr = fork_project.create_pr(
            title="test: fork(master) <- fork",
            body="pull request body",
            target_branch="master",
            source_branch="test_source",
            fork_username=user,
        )
        pr_opened_after = len(fork_project.get_pr_list(status=PRStatus.open))

        assert opened_pr.title == "test: fork(master) <- fork"
        assert opened_pr.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

        opened_pr.close()
        assert opened_pr.status == PRStatus.closed

    def test_pr_labels(self):
        """
        Remove the labels from this pr before regenerating the response files:
        https://github.com/packit/ogr/pull/1
        """
        pr = self.ogr_project.get_pr(1)
        labels = pr.labels
        assert not labels

        pr.add_label("test_lb1", "test_lb2")
        labels = pr.labels
        assert len(labels) == 2
        assert labels[0].name == "test_lb1"
        assert labels[1].name == "test_lb2"

    def test_pr_close(self):
        gh_project = self.hello_world_project
        pr = gh_project.create_pr(
            title="test pr_close",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
        )
        pr.close()
        pr_check = gh_project.get_pr(pr.id)

        assert pr_check.title == "test pr_close"
        assert pr_check.status == PRStatus.closed

    def test_pr_status(self):
        pr = self.ogr_project.get_pr(pr_id=278)

        statuses = pr.get_statuses()
        assert statuses
        assert len(statuses) >= 6

    def test_setters(self):
        pr = self.hello_world_project.get_pr(pr_id=72)

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
            self.hello_world_project.get_pr(111).head_commit
            == "1abb19255a7c1bec7ffcae2487f022b23175af2b"
        )
        assert (
            self.hello_world_project.get_pr(112).head_commit
            == "9ab13fa4b4944510022730708045f42aea106cef"
        )
        assert (
            self.hello_world_project.get_pr(113).head_commit
            == "7cf6d0cbeca285ecbeb19a0067cb243783b3c768"
        )

    def test_source_project_upstream_branch(self):
        # Tests source project for PR from upstream to upstream.
        pr = self.hello_world_project.get_pr(72)
        source_project = pr.source_project
        # The namespace was 'packit-service' when this PR was opened.
        assert source_project.namespace == "packit"
        assert source_project.repo == "hello-world"

    def test_source_project_upstream_fork(self):
        # Tests source project for PR from fork to upstream
        pr = self.hello_world_project.get_pr(111)
        source_project = pr.source_project
        assert source_project.namespace == "lbarcziova"
        assert source_project.repo == "hello-world"

    def test_source_project_fork_fork(self):
        # Tests source project for PR from fork to the fork itself
        project = self.service.get_project(repo="hello-world", namespace="mfocko")
        pr = project.get_pr(1)
        source_project = pr.source_project
        assert source_project.namespace == "mfocko"
        assert source_project.repo == "hello-world"

    def test_source_project_other_fork_fork(self):
        # Tests source project for PR from one fork to another fork
        project = self.service.get_project(
            repo="hello-world", namespace="lachmanfrantisek"
        )
        pr = project.get_pr(1)
        source_project = pr.source_project
        assert source_project.namespace == "mfocko"
        assert source_project.repo == "hello-world"

    def test_source_project_renamed_fork(self):
        """
        Tests source project for PR from fork to the upstream with renamed fork.

        1. Create PR from fork to upstream.
        2. Rename fork.
        """
        pr = self.hello_world_project.get_pr(113)
        source_project = pr.source_project
        assert source_project.namespace == "mfocko"
        assert source_project.repo == "hello-world"

    def test_source_project_renamed_upstream(self):
        """
        Tests source project for PR from to the upstream with renamed upstream.

        1. Use for example testing repo in a packit namespace
        2. Create a PR from fork to the repo.
        3. Rename the repo in packit namespace.
        """
        pr = self.service.get_project(
            repo="testing_repo_changed_name", namespace="packit"
        ).get_pr(1)
        source_project = pr.source_project
        assert source_project.namespace == self.service.user.get_username()
        assert source_project.repo == "repo_created_for_test_in_group"

    def test_commits_url(self):
        pr = self.hello_world_project.get_pr(113)
        assert (
            pr.commits_url == "https://github.com/packit/hello-world/pull/113/commits"
        )

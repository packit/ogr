import os
import unittest

from github import GithubException

from ogr import GithubService
from ogr.abstract import PRStatus, IssueStatus
from ogr.persistent_storage import PersistentObjectStorage

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class GithubTests(unittest.TestCase):
    def setUp(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.user = os.environ.get("GITHUB_USER")
        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_github_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file

        if PersistentObjectStorage().is_write_mode and (
            not self.user or not self.token
        ):
            raise EnvironmentError("please set GITHUB_TOKEN GITHUB_USER env variables")

        self.service = GithubService(token=self.token)

        self.hello_world_project = self.service.get_project(
            namespace="packit-service", repo="hello-world"
        )
        self.colin_project = self.service.get_project(
            namespace="user-cont", repo="colin"
        )
        self.colin_fork = self.service.get_project(
            namespace="user-cont", repo="colin", is_fork=True
        )

        self.not_forked_project = self.service.get_project(
            namespace="fedora-modularity", repo="fed-to-brew"
        )

    def tearDown(self):
        PersistentObjectStorage().dump()


class Comments(GithubTests):
    def test_pr_comments(self):
        pr_comments = self.colin_project.get_pr_comments(7)
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[0].comment.endswith("I've just integrated your thoughts.")
        assert pr_comments[1].comment.startswith("Thank you!")

    def test_pr_comments_reversed(self):
        pr_comments = self.colin_project.get_pr_comments(7, reverse=True)
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[0].comment.startswith("Thank you!")

    def test_pr_comments_filter(self):
        pr_comments = self.colin_project.get_pr_comments(7, filter_regex="Thank")
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[1].comment.startswith("Thank you!")

        pr_comments = self.colin_project.get_pr_comments(
            7, filter_regex="Thank you for the ([a-z]*)"
        )
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].comment.endswith("thoughts.")

    def test_pr_comments_search(self):
        comment_match = self.colin_project.search_in_pr(7, filter_regex="Thank")
        assert comment_match
        assert comment_match[0] == "Thank"

        comment_match = self.colin_project.search_in_pr(
            7, filter_regex="Thank you for the ([a-z]*)"
        )
        assert comment_match
        assert comment_match[0] == "Thank you for the review"
        assert comment_match[1] == "review"


class GenericCommands(GithubTests):
    def test_description(self):
        description = self.colin_project.get_description()
        assert description.startswith("Tool to check generic")

    def test_branches(self):
        branches = self.colin_project.get_branches()
        assert branches
        assert set(branches) == {"master", "overriden-labels-check"}

    def test_git_urls(self):
        urls = self.colin_project.get_git_urls()
        assert urls
        assert len(urls) == 2
        assert "git" in urls
        assert "ssh" in urls
        assert urls["git"] == "https://github.com/user-cont/colin.git"
        assert urls["ssh"].endswith("git@github.com:user-cont/colin.git")

    def test_username(self):
        # changed to check just lenght, because it is based who regenerated data files
        assert len(self.service.user.get_username()) > 3

    def test_get_file(self):
        file_content = self.colin_project.get_file_content(".gitignore")
        assert file_content
        assert isinstance(file_content, str)
        assert "*.py[co]" in file_content

    def test_nonexisting_file(self):
        with self.assertRaises(FileNotFoundError):
            self.colin_project.get_file_content(".blablabla_nonexisting_file")

    def test_parent_project(self):
        assert self.colin_fork.parent.namespace == "user-cont"
        assert self.colin_fork.parent.repo == "colin"

    @unittest.skip("get_commit_flags not implemented")
    def test_commit_flags(self):
        flags = self.colin_project.get_commit_flags(
            commit="d87466de81c72231906a6597758f37f28830bb71"
        )
        assert isinstance(flags, list)
        assert len(flags) == 0

    def test_get_sha_from_tag(self):
        assert (
            self.colin_project.get_sha_from_tag("v0.0.1")
            == "4fde179d43b6c9c6a8c4d0c869293d18a6ce7ddc"
        )
        assert not self.colin_project.get_sha_from_tag("future")

    def test_get_tag_from_tag_name(self):
        tag = self.colin_project.get_tag_from_tag_name("v0.0.1")
        assert tag.name == "v0.0.1"
        assert tag.commit_sha == "4fde179d43b6c9c6a8c4d0c869293d18a6ce7ddc"

    def test_get_tag_from_nonexisting_tag_name(self):
        assert not self.colin_project.get_tag_from_tag_name("future")

    def test_get_owners(self):
        owners = self.colin_project.get_owners()
        assert ["user-cont"] == owners

    def test_issue_permissions(self):
        users = self.colin_project.who_can_close_issue()
        assert "usercont-release-bot" in users

        issue = self.colin_project.get_issue_info(1)
        assert self.colin_project.can_close_issue("usercont-release-bot", issue)
        assert not self.colin_project.can_close_issue("marusinm", issue)

    def test_pr_permissions(self):
        users = self.colin_project.who_can_merge_pr()
        assert "usercont-release-bot" in users

        assert self.colin_project.can_merge_pr("usercont-release-bot")
        assert not self.colin_project.can_merge_pr("marusinm")


class Issues(GithubTests):
    def test_issue_list(self):
        issue_list = self.colin_fork.get_issue_list()
        assert isinstance(issue_list, list)
        assert not issue_list

        issue_list_all = self.colin_project.get_issue_list(status=IssueStatus.all)
        assert issue_list_all
        assert len(issue_list_all) >= 144

        issue_list_closed = self.colin_project.get_issue_list(status=IssueStatus.closed)
        assert issue_list_closed
        assert len(issue_list_closed) >= 140

        issue_list = self.colin_project.get_issue_list()
        assert issue_list
        assert len(issue_list) >= 2

    def test_issue_info(self):
        issue_info = self.colin_project.get_issue_info(issue_id=2)
        assert issue_info
        assert issue_info.title.startswith("add basic readme")
        assert issue_info.status == IssueStatus.closed

    def test_issue_labels(self):
        labels = self.colin_project.get_issue_labels(issue_id=6)
        assert not labels
        self.colin_project.add_issue_labels(issue_id=6, labels=["test_lb1", "test_lb2"])
        labels = self.colin_project.get_issue_labels(issue_id=6)
        assert len(labels) == 2
        assert labels[0].name == "test_lb1"
        assert labels[1].name == "test_lb2"


class PullRequests(GithubTests):
    def test_pr_list(self):
        pr_list = self.colin_fork.get_pr_list()
        assert isinstance(pr_list, list)
        assert not pr_list

        pr_list_all = self.colin_project.get_pr_list(status=PRStatus.all)
        assert pr_list_all
        assert len(pr_list_all) >= 144

        pr_list_closed = self.colin_project.get_pr_list(status=PRStatus.closed)
        assert pr_list_closed
        assert len(pr_list_closed) >= 140
        closed_pr_numbers = []
        for closed_pr in pr_list_closed:
            closed_pr_numbers.append(closed_pr.id)
        assert 23 in closed_pr_numbers

        pr_list_merged = self.colin_project.get_pr_list(status=PRStatus.merged)
        assert pr_list_merged
        assert len(pr_list_merged) >= 1
        closed_pr_numbers = []
        for closed_pr in pr_list_merged:
            closed_pr_numbers.append(closed_pr.id)
        assert 23 not in closed_pr_numbers

        pr_list = self.colin_project.get_pr_list()
        assert pr_list
        assert len(pr_list) >= 1

    def test_pr_info(self):
        pr_info = self.colin_project.get_pr_info(pr_id=1)
        assert pr_info
        assert pr_info.title.startswith("new")
        assert pr_info.status == PRStatus.merged

    def test_update_pr_info(self):
        self.colin_project.update_pr_info(
            pr_id=1, title="changed", description="changed description"
        )
        pr_info = self.colin_project.get_pr_info(pr_id=1)
        assert pr_info.title == "changed"
        assert pr_info.description == "changed description"

        self.colin_project.update_pr_info(
            pr_id=1, title="new", description="new description"
        )
        pr_info = self.colin_project.get_pr_info(pr_id=1)
        assert pr_info.title == "new"
        assert pr_info.description == "new description"

    def test_pr_labels(self):
        labels = self.colin_project.get_pr_labels(pr_id=1)
        assert not labels
        self.colin_project.add_pr_labels(pr_id=1, labels=["test_lb1", "test_lb2"])
        labels = self.colin_project.get_pr_labels(pr_id=1)
        assert len(labels) == 2
        assert labels[0].name == "test_lb1"
        assert labels[1].name == "test_lb2"


class Releases(GithubTests):
    def test_get_releases(self):
        releases = self.colin_project.get_releases()
        assert releases

        assert len(releases) >= 9

    def test_create_release(self):
        count_before = len(self.hello_world_project.get_releases())
        release = self.hello_world_project.create_release(
            tag="0.4.1", name="test", message="testing release"
        )
        count_after = len(self.hello_world_project.get_releases())
        assert release.tag_name == "0.4.1"
        assert release.title == "test"
        assert release.body == "testing release"
        assert count_before + 1 == count_after

    def test_latest_release(self):
        release = self.hello_world_project.get_latest_release()
        assert release.tag_name == "0.4.1"
        assert release.title == "test"
        assert release.body == "testing release"


class Forks(GithubTests):
    def test_fork(self):
        assert self.colin_fork.is_fork is True
        fork_description = self.colin_fork.get_description()
        assert fork_description

    @unittest.skip(
        "not working with yaml file because it  check exception within setup"
    )
    def test_nonexisting_fork(self):
        self.colin_nonexisting_fork = self.service.get_project(
            repo="omfeprkfmwpefmwpefkmwpeofjwepof", is_fork=True
        )
        with self.assertRaises(GithubException) as ex:
            self.colin_nonexisting_fork.get_description()
        s = str(ex.value.args)
        assert "Not Found" in s
        assert "404" in s

    def test_get_fork(self):
        fork = self.colin_project.get_fork()
        assert fork
        assert fork.get_description()

    def test_is_fork(self):
        assert not self.colin_project.is_fork
        is_forked = self.colin_project.is_forked()
        assert isinstance(is_forked, bool)
        # `is True` is here on purpose: we want to be sure that .is_forked() returns True object
        # because Tomas had his crazy ideas and wanted to return GitProject directly,
        # stop that madman
        assert is_forked is True
        fork = self.colin_project.get_fork(create=False)
        assert fork
        assert fork.is_fork

    def test_create_fork(self):
        not_existing_fork = self.not_forked_project.get_fork(create=False)
        assert not not_existing_fork
        assert not self.not_forked_project.is_forked()

        old_forks = self.not_forked_project.service.user.get_forks()

        self.not_forked_project.fork_create()

        assert self.not_forked_project.get_fork().get_description()
        assert self.not_forked_project.is_forked()

        new_forks = self.not_forked_project.service.user.get_forks()
        assert len(old_forks) == len(new_forks) - 1

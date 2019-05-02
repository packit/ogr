import os
import unittest
from github import GithubException

from ogr.abstract import PRStatus
from ogr.services.github import GithubService
from ogr.mock_core import PersistentObjectStorage

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class GithubTests(unittest.TestCase):
    def setUp(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.user = os.environ.get("GITHUB_USER")
        test_name = self.id() or "all"
        self.is_write_mode = bool(os.environ.get("FORCE_WRITE"))
        if self.is_write_mode and (not self.user or not self.token):
            raise EnvironmentError("please set GITHUB_TOKEN GITHUB_USER env variables")
        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_github_data_{test_name}.yaml"
        )
        self.service = GithubService(
            token=self.token,
            persistent_storage=PersistentObjectStorage(
                persistent_data_file, self.is_write_mode
            ),
        )
        self.colin_project = self.service.get_project(
            namespace="user-cont", repo="colin"
        )
        self.colin_fork = self.service.get_project(
            namespace="user-cont", repo="colin", is_fork=True
        )

    def tearDown(self):
        self.service.persistent_storage.dump()


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

    def test_get_releases(self):
        releases = self.colin_project.get_releases()
        assert releases

        assert len(releases) >= 9

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

        pr_list = self.colin_project.get_pr_list()
        assert pr_list
        assert len(pr_list) >= 2

    def test_pr_info(self):
        pr_info = self.colin_project.get_pr_info(pr_id=1)
        assert pr_info
        assert pr_info.title.startswith("Add basic structure")
        assert pr_info.status == PRStatus.closed


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

    @unittest.skip("does not work when you don't have fork already created")
    def test_create_fork(self):
        not_existing_fork = self.colin_project.get_fork()
        assert not not_existing_fork
        self.colin_project.fork_create()
        assert self.colin_project.get_fork().exists()

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

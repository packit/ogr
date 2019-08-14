import os
import unittest

from ogr.services.gitlab import GitlabService
from ogr.persistent_storage import PersistentObjectStorage

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class GitlabTests(unittest.TestCase):
    def setUp(self):
        self.token = os.environ.get("GITLAB_TOKEN")
        self.user = os.environ.get("GITLAB_USER")
        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_gitlab_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file

        if PersistentObjectStorage().is_write_mode and (
            not self.user or not self.token
        ):
            raise EnvironmentError("please set GITLAB_TOKEN GITLAB_USER env variables")

        self.service = GitlabService(
            token=self.token, url="https://gitlab.cee.redhat.com"
        )

        self.project = self.service.get_project(
            repo="testing-ogr-repo", namespace="lbarczio"
        )
        self.packit_project = self.service.get_project(
            repo="packit-service", namespace="user-cont"
        )

    def tearDown(self):
        PersistentObjectStorage().dump()


class GenericCommands(GitlabTests):
    def test_branches(self):
        branches = self.project.get_branches()
        assert branches
        assert "master" in branches

    def test_get_file(self):
        file_content = self.project.get_file_content("README.md")
        assert file_content
        assert "New README" in file_content

    def test_nonexisting_file(self):
        with self.assertRaises(FileNotFoundError):
            self.project.get_file_content(".blablabla_nonexisting_file")

    def test_username(self):
        # check just lenght, because it is based who regenerated data files
        assert len(self.service.user.get_username()) > 3

    def test_email(self):
        email = self.service.user.get_email()
        assert email
        assert len(email) > 3
        assert "@" in email
        assert "." in email

    def test_get_forks(self):
        forks = self.packit_project.get_forks()
        assert forks[0].namespace == "lbarczio"
        assert forks[0].repo == "packit-service"


class Issues(GitlabTests):
    def test_get_issue_list(self):
        issue_list = self.project.get_issue_list()
        assert issue_list
        assert len(issue_list) >= 1

    def test_issue_info(self):
        issue_info = self.project.get_issue_info(issue_id=1)
        assert issue_info
        assert issue_info.title.startswith("My first issue")
        assert issue_info.description.startswith("This is testing issue")

    def test_get_all_issue_comments(self):
        comments = self.packit_project._get_all_issue_comments(issue_id=3)
        assert comments[1].comment.startswith("Fixed")
        assert comments[1].author == "jpopelka"
        assert len(comments) == 3

    def test_create_issue(self):
        issue = self.project.create_issue(
            title="Issue 1", description="Description for issue 1"
        )
        assert issue.title == "Issue 1"
        assert issue.description == "Description for issue 1"

    def test_close_issue(self):
        issue = self.project.close_issue(issue_id=1)
        assert issue.status == "closed"


class PullRequests(GitlabTests):
    def test_pr_list(self):
        pr_list = self.packit_project.list_pull_requests()
        assert pr_list
        assert len(pr_list) >= 20

    def test_pr_info(self):
        pr_info = self.packit_project.get_pr_info(pr_id=1)
        assert pr_info
        assert pr_info.title.startswith("Add image")
        assert pr_info.description.startswith("Requires")

    def test_get_all_pr_commits(self):
        commits = self.packit_project.get_all_pr_commits(pr_id=6)
        assert commits[0] == "8764b13154f3f415a97c872b217c7b502f30bd3f"
        assert commits[1] == "e6b7f1604ee12e93021c81c2786369116d7ab3fe"
        assert len(commits) == 5

    def test_get_all_pr_comments(self):
        comments = self.packit_project._get_all_pr_comments(pr_id=21)
        assert comments[2].comment.startswith("so, ansible")
        assert comments[2].author == "ttomecek"
        assert len(comments) == 5

    def test_update_pr_info(self):
        pr_info = self.project.get_pr_info(pr_id=1)
        original_description = pr_info.description

        self.project.update_pr_info(pr_id=1, description="changed description")
        pr_info = self.project.get_pr_info(pr_id=1)
        assert pr_info.description == "changed description"

        self.project.update_pr_info(pr_id=1, description=original_description)
        pr_info = self.project.get_pr_info(pr_id=1)
        assert pr_info.description == original_description


class Releases(GitlabTests):
    def test_get_releases(self):
        releases = self.project.get_releases()
        assert releases
        count = len(releases)
        assert count >= 1
        assert releases[count - 1].title == "test"
        assert releases[count - 1].tag_name == "0.1.0"
        assert releases[count - 1].body == "testing release"

    def test_create_release(self):
        count_before = len(self.project.get_releases())
        release = self.project.create_release(
            name="test", tag_name="0.3.0", description="testing release", ref="master"
        )
        count_after = len(self.project.get_releases())
        assert release.tag_name == "0.3.0"
        assert release.title == "test"
        assert release.body == "testing release"
        assert count_before + 1 == count_after

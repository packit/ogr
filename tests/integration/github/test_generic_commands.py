from datetime import datetime

from github import GithubException
import pytest
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base import GithubTests
from ogr.abstract import AccessLevel, CommitStatus
from ogr.exceptions import GithubAPIException


@record_requests_for_all_methods()
class GenericCommands(GithubTests):
    def test_add_user(self):
        """
        Make sure you have `playground` repo in your own namespace and
        `lachmanfrantisek` is not added in the project before running tests
        """
        project = self.service.get_project(
            repo="playground", namespace=self.service.user.get_username()
        )

        assert not project.can_merge_pr("lachmanfrantisek")
        project.add_user("lachmanfrantisek", AccessLevel.pull)

    def test_description(self):
        description = self.ogr_project.get_description()
        assert description.startswith("One Git library to Rule")

    def test_branches(self):
        branches = self.ogr_project.get_branches()
        assert branches
        assert {"master"}.issubset(set(branches))

    def test_git_urls(self):
        urls = self.ogr_project.get_git_urls()
        assert urls
        assert len(urls) == 2
        assert "git" in urls
        assert "ssh" in urls
        assert urls["git"] == "https://github.com/packit/ogr.git"
        assert urls["ssh"].endswith("git@github.com:packit/ogr.git")

    def test_username(self):
        # changed to check just lenght, because it is based who regenerated data files
        assert len(self.service.user.get_username()) > 3

    def test_email(self):
        test_str = self.service.user.get_email()
        assert test_str
        assert len(test_str) > 0
        assert "@" in test_str
        assert "." in test_str

    def test_get_file(self):
        file_content = self.ogr_project.get_file_content(".git_archival.txt")
        assert file_content
        assert isinstance(file_content, str)
        assert "ref-names:" in file_content

    def test_get_files(self):
        files = self.ogr_project.get_files()
        assert files
        assert len(files) >= 10
        assert ".git_archival.txt" in files

        files = self.ogr_project.get_files(filter_regex=".*.spec", recursive=True)
        assert files
        assert len(files) >= 1
        assert any("python-ogr.spec" in f for f in files)

    def test_nonexisting_file(self):
        with self.assertRaises(FileNotFoundError):
            self.ogr_project.get_file_content(".blablabla_nonexisting_file")

    def test_parent_project(self):
        assert self.ogr_fork.parent.namespace == "packit"
        assert self.ogr_fork.parent.repo == "ogr"

    def test_commit_flags(self):
        flags = self.ogr_project.get_commit_statuses(
            commit="29ca3caefc781b4b41245df3e01086ffa4b4639e"
        )
        assert isinstance(flags, list)
        assert len(flags) == 0

    def test_get_sha_from_tag(self):
        assert (
            self.ogr_project.get_sha_from_tag("0.0.1")
            == "29ca3caefc781b4b41245df3e01086ffa4b4639e"
        )
        with pytest.raises(GithubAPIException) as ex:
            self.ogr_project.get_sha_from_tag("future")
        assert "not found" in str(ex.value)

    def test_get_tag_from_tag_name(self):
        tag = self.ogr_project.get_tag_from_tag_name("0.0.1")
        assert tag.name == "0.0.1"
        assert tag.commit_sha == "29ca3caefc781b4b41245df3e01086ffa4b4639e"

    def test_get_tag_from_nonexisting_tag_name(self):
        assert not self.ogr_project.get_tag_from_tag_name("future")

    def test_get_tags(self):
        tags = self.ogr_project.get_tags()

        names = {f"0.{i}.0" for i in range(1, 10)}
        names.update({"0.0.1", "0.0.2", "0.0.3", "0.3.1"})
        assert names <= set(map(lambda tag: tag.name, tags))

        commits = {
            "ef947cd637f5fa0c28ffca71798d9e61b24880d8",
            "64a9207afbb83c1e20659ddecd1e07303ad1ddf2",
            "29ca3caefc781b4b41245df3e01086ffa4b4639e",
            "059d21080a7849acff4626b6e0ec61830d537ac4",
            "088158211481a025a20f3abe716359624615b66e",
        }
        assert commits < set(map(lambda tag: tag.commit_sha, tags))

    def test_get_owners(self):
        owners = self.ogr_project.get_owners()
        assert ["packit"] == owners

    def test_issue_permissions(self):
        users = self.ogr_project.who_can_close_issue()
        assert "lachmanfrantisek" in users

        issue = self.ogr_project.get_issue(4)
        assert issue.can_close("lachmanfrantisek")

    def test_issue_permissions_cant_close(self):
        issue = self.ogr_project.get_issue(4)
        assert not issue.can_close("unknown_user")

    def test_pr_permissions(self):
        users = self.ogr_project.who_can_merge_pr()
        assert "lachmanfrantisek" in users

        assert self.ogr_project.can_merge_pr("lachmanfrantisek")
        # can_merge_pr() requires an existing user,
        # otherwise the GitHub API fails with 'not a user'
        assert not self.ogr_project.can_merge_pr("torvalds")

    def test_set_commit_status(self):
        status = self.ogr_project.set_commit_status(
            commit="c891a9e4ac01e6575f3fd66cf1b7db2f52f10128",
            state=CommitStatus.success,
            target_url="https://github.com/packit/ogr",
            description="testing description",
            context="test",
            trim=True,
        )
        assert status
        assert status.comment == "testing description"

    def test_get_commit_statuses(self):
        commit = "c891a9e4ac01e6575f3fd66cf1b7db2f52f10128"
        statuses = self.ogr_project.get_commit_statuses(commit=commit)
        assert statuses
        assert len(statuses) >= 26
        last_flag = statuses[-1]
        assert last_flag.comment.startswith("Testing the trimming")
        assert last_flag.url == "https://github.com/packit-service/ogr"
        assert last_flag.commit == commit
        assert last_flag.state == CommitStatus.success
        assert last_flag.context == "test"
        assert last_flag.uid
        assert last_flag.created == datetime(
            year=2019, month=9, day=19, hour=12, minute=21, second=6
        )
        assert last_flag.edited == datetime(
            year=2019, month=9, day=19, hour=12, minute=21, second=6
        )

    def test_set_commit_status_long_description(self):
        long_description = (
            "Testing the trimming of the description after an argument trim "
            "is added. The argument defaults to False, but in packit the"
            " argument trim is set to True."
        )
        with pytest.raises(GithubException):
            self.ogr_project.set_commit_status(
                commit="c891a9e4ac01e6575f3fd66cf1b7db2f52f10128",
                state=CommitStatus.success,
                target_url="https://github.com/packit/ogr",
                description=long_description,
                context="test",
            )

        status = self.ogr_project.set_commit_status(
            commit="c891a9e4ac01e6575f3fd66cf1b7db2f52f10128",
            state=CommitStatus.success,
            target_url="https://github.com/packit/ogr",
            description=long_description,
            context="test",
            trim=True,
        )
        assert status
        assert len(status.comment) == 140

    def test_get_web_url(self):
        url = self.ogr_project.get_web_url()
        assert url == "https://github.com/packit/ogr"

    def test_full_repo_name(self):
        assert self.ogr_project.full_repo_name == "packit/ogr"

    def test_project_exists(self):
        assert self.ogr_project.exists()

    def test_project_not_exists(self):
        assert not self.service.get_project(
            repo="some-non-existing-repo", namespace="some-none-existing-namespace"
        ).exists()

    def test_is_private(self):
        # The repository bellow needs to be a private repository which can be
        # accessed by the user who's GITHUB_TOKEN is used for
        # test regeneration.
        private_project = self.service.get_project(
            namespace=self.service.user.get_username(), repo="playground"
        )
        assert private_project.is_private()

    def test_is_not_private(self):
        assert not self.ogr_project.is_private()

    def test_delete(self):
        project = self.service.get_project(
            repo="delete-project", namespace="shreyaspapi"
        )
        project.delete()

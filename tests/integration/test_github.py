import os
import unittest

import pytest
from github import GithubException, UnknownObjectException

from ogr import GithubService
from ogr.abstract import PRStatus, IssueStatus
from ogr.exceptions import GithubAPIException
from requre.storage import PersistentObjectStorage

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class GithubTests(unittest.TestCase):
    def setUp(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_github_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file

        if PersistentObjectStorage().is_write_mode and (not self.token):
            raise EnvironmentError("please set GITHUB_TOKEN env variables")

        self.service = GithubService(token=self.token)
        self._ogr_project = None
        self._ogr_fork = None
        self._hello_world_project = None
        self._not_forked_project = None

    @property
    def ogr_project(self):
        if not self._ogr_project:
            self._ogr_project = self.service.get_project(
                namespace="packit-service", repo="ogr"
            )
        return self._ogr_project

    @property
    def ogr_fork(self):
        if not self._ogr_fork:
            self._ogr_fork = self.service.get_project(
                namespace="packit-service", repo="ogr", is_fork=True
            )
        return self._ogr_fork

    @property
    def hello_world_project(self):
        if not self._hello_world_project:
            self._hello_world_project = self.service.get_project(
                namespace="packit-service", repo="hello-world"
            )
        return self._hello_world_project

    @property
    def not_forked_project(self):
        if not self._not_forked_project:
            self._not_forked_project = self.service.get_project(
                namespace="fedora-modularity", repo="fed-to-brew"
            )
        return self._not_forked_project

    def tearDown(self):
        PersistentObjectStorage().dump()


class Comments(GithubTests):
    def test_pr_comments(self):
        pr_comments = self.ogr_project.get_pr_comments(9)
        assert pr_comments
        assert len(pr_comments) == 2

        assert pr_comments[0].comment.endswith("fixed")
        assert pr_comments[1].comment.startswith("LGTM")

    def test_pr_comments_reversed(self):
        pr_comments = self.ogr_project.get_pr_comments(9, reverse=True)
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[0].comment.startswith("LGTM")

    def test_pr_comments_filter(self):
        pr_comments = self.ogr_project.get_pr_comments(9, filter_regex="fixed")
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].comment.startswith("@TomasTomecek")

        pr_comments = self.ogr_project.get_pr_comments(
            9, filter_regex="LGTM, nicely ([a-z]*)"
        )
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].comment.endswith("done!")

    def test_pr_comments_search(self):
        comment_match = self.ogr_project.search_in_pr(9, filter_regex="LGTM")
        assert comment_match
        assert comment_match[0] == "LGTM"

        comment_match = self.ogr_project.search_in_pr(
            9, filter_regex="LGTM, nicely ([a-z]*)"
        )
        assert comment_match
        assert comment_match[0] == "LGTM, nicely done"

    def test_issue_comments(self):
        comments = self.ogr_project.get_issue_comments(194)
        assert len(comments) == 6
        assert comments[0].comment.startswith("/packit")

    def test_issue_comments_reversed(self):
        comments = self.ogr_project.get_issue_comments(194, reverse=True)
        assert len(comments) == 6
        assert comments[0].comment.startswith("The ")

    def test_issue_comments_regex(self):
        comments = self.ogr_project.get_issue_comments(
            194, filter_regex=r".*Fedora package.*"
        )
        assert len(comments) == 3
        assert "master" in comments[0].comment

    def test_issue_comments_regex_reversed(self):
        comments = self.ogr_project.get_issue_comments(
            194, reverse=True, filter_regex=".*Fedora package.*"
        )
        assert len(comments) == 3
        assert "f29" in comments[0].comment

    def test_pr_comments_author_regex(self):
        comments = self.ogr_project.get_pr_comments(
            217, filter_regex="^I", author="mfocko"
        )
        assert len(comments) == 1
        assert "API" in comments[0].comment

    def test_pr_comments_author(self):
        comments = self.ogr_project.get_pr_comments(217, author="lachmanfrantisek")
        assert len(comments) == 3
        assert comments[0].comment.endswith("here.")

    def test_issue_comments_author_regex(self):
        comments = self.ogr_project.get_issue_comments(
            220, filter_regex=".*API.*", author="lachmanfrantisek"
        )
        assert len(comments) == 1
        assert comments[0].comment.startswith("After")

    def test_issue_comments_author(self):
        comments = self.ogr_project.get_issue_comments(220, author="mfocko")
        assert len(comments) == 2
        assert comments[0].comment.startswith("What")
        assert comments[1].comment.startswith("Consider")


class GenericCommands(GithubTests):
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
        assert urls["git"] == "https://github.com/packit-service/ogr.git"
        assert urls["ssh"].endswith("git@github.com:packit-service/ogr.git")

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

    def test_nonexisting_file(self):
        with self.assertRaises(FileNotFoundError):
            self.ogr_project.get_file_content(".blablabla_nonexisting_file")

    def test_parent_project(self):
        assert self.ogr_fork.parent.namespace == "packit-service"
        assert self.ogr_fork.parent.repo == "ogr"

    @unittest.skip("get_commit_flags not implemented")
    def test_commit_flags(self):
        flags = self.ogr_project.get_commit_flags(
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

    def test_get_owners(self):
        owners = self.ogr_project.get_owners()
        assert ["packit-service"] == owners

    def test_issue_permissions(self):
        users = self.ogr_project.who_can_close_issue()
        assert "lachmanfrantisek" in users

        issue = self.ogr_project.get_issue_info(4)
        assert self.ogr_project.can_close_issue("lachmanfrantisek", issue)
        assert not self.ogr_project.can_close_issue("unknown_user", issue)

    def test_pr_permissions(self):
        users = self.ogr_project.who_can_merge_pr()
        assert "lachmanfrantisek" in users

        assert self.ogr_project.can_merge_pr("lachmanfrantisek")
        assert not self.ogr_project.can_merge_pr("unknown_user")

    def test_set_commit_status(self):
        status = self.ogr_project.set_commit_status(
            commit="c891a9e4ac01e6575f3fd66cf1b7db2f52f10128",
            state="success",
            target_url="https://github.com/packit-service/ogr",
            description="testing description",
            context="test",
            trim=True,
        )
        assert status
        assert status.comment == "testing description"

    def test_set_commit_status_long_description(self):
        long_description = (
            "Testing the trimming of the description after an argument trim "
            "is added. The argument defaults to False, but in packit-service the"
            " argument trim is set to True."
        )
        with pytest.raises(GithubException):
            self.ogr_project.set_commit_status(
                commit="c891a9e4ac01e6575f3fd66cf1b7db2f52f10128",
                state="success",
                target_url="https://github.com/packit-service/ogr",
                description=long_description,
                context="test",
            )

        status = self.ogr_project.set_commit_status(
            commit="c891a9e4ac01e6575f3fd66cf1b7db2f52f10128",
            state="success",
            target_url="https://github.com/packit-service/ogr",
            description=long_description,
            context="test",
            trim=True,
        )
        assert status
        assert len(status.comment) == 140

    def test_get_web_url(self):
        url = self.ogr_project.get_web_url()
        assert url == "https://github.com/packit-service/ogr"

    def test_full_repo_name(self):
        assert self.ogr_project.full_repo_name == "packit-service/ogr"


class Issues(GithubTests):
    def test_issue_list(self):
        issue_list = self.ogr_fork.get_issue_list()
        assert isinstance(issue_list, list)
        assert not issue_list

        issue_list_all = self.ogr_project.get_issue_list(status=IssueStatus.all)
        assert issue_list_all
        assert len(issue_list_all) >= 45

        issue_list_closed = self.ogr_project.get_issue_list(status=IssueStatus.closed)
        assert issue_list_closed
        assert len(issue_list_closed) >= 35

        issue_list = self.ogr_project.get_issue_list()
        assert issue_list
        assert len(issue_list) >= 3

    def test_issue_info(self):
        issue_info = self.ogr_project.get_issue_info(issue_id=4)
        assert issue_info
        assert issue_info.title.startswith("Better name")
        assert issue_info.status == IssueStatus.closed

    def test_issue_labels(self):
        """
        Remove the labels from this issue before regenerating the response files:
        https://github.com/packit-service/ogr/issues/4
        """
        labels = self.ogr_project.get_issue_labels(issue_id=4)

        assert not labels
        self.ogr_project.add_issue_labels(issue_id=4, labels=["test_lb1", "test_lb2"])
        labels = self.ogr_project.get_issue_labels(issue_id=4)
        assert len(labels) == 2
        assert labels[0].name == "test_lb1"
        assert labels[1].name == "test_lb2"

    def test_list_contains_only_issues(self):
        issue_list_all = self.ogr_project.get_issue_list(status=IssueStatus.all)
        issue_ids = [issue.id for issue in issue_list_all]

        pr_ids = [219, 207, 201, 217, 208, 210]
        for id in pr_ids:
            assert id not in issue_ids

    def test_functions_fail_for_pr(self):
        with pytest.raises(GithubAPIException):
            self.ogr_project.get_issue_info(issue_id=1)
        with pytest.raises(GithubAPIException):
            self.ogr_project.issue_comment(issue_id=1, body="should fail")
        with pytest.raises(GithubAPIException):
            self.ogr_project.issue_close(issue_id=1)
        with pytest.raises(GithubAPIException):
            self.ogr_project.get_issue_labels(issue_id=1)
        with pytest.raises(GithubAPIException):
            self.ogr_project.add_issue_labels(issue_id=1, labels=["should fail"])


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
        pr_info = self.ogr_project.get_pr_info(pr_id=1)
        assert pr_info
        assert pr_info.title == "WIP: API"
        assert pr_info.status == PRStatus.merged
        assert pr_info.url == "https://github.com/packit-service/ogr/pull/1"
        assert pr_info.diff_url == "https://github.com/packit-service/ogr/pull/1/files"

    def test_all_pr_commits(self):
        commits = self.ogr_project.get_all_pr_commits(pr_id=1)
        assert len(commits) == 3
        assert commits[0] == "431f4a7c5cce24c3035b17c5131a3918ab989bd0"
        assert commits[2] == "5d6cc05d30ef0a0d69bb42bdcaad187408a070b0"

    def test_update_pr_info(self):
        pr_info = self.ogr_project.get_pr_info(pr_id=1)
        orig_title = pr_info.title
        orig_description = pr_info.description

        self.ogr_project.update_pr_info(
            pr_id=1, title="changed", description="changed description"
        )
        pr_info = self.ogr_project.get_pr_info(pr_id=1)
        assert pr_info.title == "changed"
        assert pr_info.description == "changed description"

        self.ogr_project.update_pr_info(
            pr_id=1, title=orig_title, description=orig_description
        )
        pr_info = self.ogr_project.get_pr_info(pr_id=1)
        assert pr_info.title == orig_title
        assert pr_info.description == orig_description

    def test_pr_create_upstream_upstream(self):
        """
        Requires  packit_service:test_source to be ahead of packit_service:test_target
        at least by one commit.
        """
        gh_project = self.hello_world_project
        pr_opened_before = len(gh_project.get_pr_list(status=PRStatus.open))
        pr_upstream_upstream = gh_project.pr_create(
            title="test: upstream <- upstream",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
        )
        pr_opened_after = len(gh_project.get_pr_list(status=PRStatus.open))
        gh_project.pr_close(pr_upstream_upstream.id)

        assert pr_upstream_upstream.title == "test: upstream <- upstream"
        assert pr_upstream_upstream.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

    def test_pr_create_upstream_forkusername(self):
        """
        Requires  packit_service:test_source to be ahead of packit_service:test_target
        at least by one commit.
        """

        gh_project = self.hello_world_project
        pr_opened_before = len(gh_project.get_pr_list(status=PRStatus.open))
        pr_upstream_forkusername = gh_project.pr_create(
            title="test: upstream <- fork_username:source_branch",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
            fork_username=self.hello_world_project.service.user.get_username(),
        )
        pr_opened_after = len(gh_project.get_pr_list(status=PRStatus.open))
        gh_project.pr_close(pr_upstream_forkusername.id)

        assert (
            pr_upstream_forkusername.title
            == "test: upstream <- fork_username:source_branch"
        )
        assert pr_upstream_forkusername.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

    def test_pr_create_upstream_fork(self):
        """
        Requires  packit_service:test_source to be ahead of packit_service:test_target
        at least by one commit.
        """

        gh_project = self.hello_world_project
        pr_opened_before = len(gh_project.get_pr_list(status=PRStatus.open))
        pr_upstream_fork = gh_project.get_fork().pr_create(
            title="test: upstream <- fork",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
        )
        pr_opened_after = len(gh_project.get_pr_list(status=PRStatus.open))
        gh_project.pr_close(pr_upstream_fork.id)

        assert pr_upstream_fork.title == "test: upstream <- fork"
        assert pr_upstream_fork.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

    def test_pr_create_fork_fu_ignored(self):
        """
        Requires  packit_service:test_source to be ahead of packit_service:test_target
        at least by one commit.
        """
        gh_project = self.hello_world_project
        pr_opened_before = len(gh_project.get_pr_list(status=PRStatus.open))
        pr_upstream_fork_fu_ignored = gh_project.get_fork().pr_create(
            title="test: upstream <- fork (fork_username ignored)",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
            fork_username=self.hello_world_project.service.user.get_username(),
        )
        pr_opened_after = len(gh_project.get_pr_list(status=PRStatus.open))
        gh_project.pr_close(pr_upstream_fork_fu_ignored.id)

        assert (
            pr_upstream_fork_fu_ignored.title
            == "test: upstream <- fork (fork_username ignored)"
        )
        assert pr_upstream_fork_fu_ignored.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

    def test_pr_labels(self):
        """
        Remove the labels from this pr before regenerating the response files:
        https://github.com/packit-service/ogr/pull/1
        """
        labels = self.ogr_project.get_pr_labels(pr_id=1)
        assert not labels
        self.ogr_project.add_pr_labels(pr_id=1, labels=["test_lb1", "test_lb2"])
        labels = self.ogr_project.get_pr_labels(pr_id=1)
        assert len(labels) == 2
        assert labels[0].name == "test_lb1"
        assert labels[1].name == "test_lb2"

    def test_pr_close(self):
        gh_project = self.hello_world_project
        pr = gh_project.pr_create(
            title="test pr_close",
            body="pull request body",
            target_branch="test_target",
            source_branch="test_source",
        )
        gh_project.pr_close(pr.id)
        pr_check = gh_project.get_pr_info(pr.id)

        assert pr_check.title == "test pr_close"
        assert pr_check.status == PRStatus.closed


class Releases(GithubTests):
    def test_get_release(self):
        release = self.hello_world_project.get_release(tag_name="0.4.1")
        assert release.title == "test"
        assert release.body == "testing release"

    def test_get_releases(self):
        releases = self.ogr_project.get_releases()
        assert releases

        assert len(releases) >= 9

    def test_create_release(self):
        """
        Raise the number in `tag` when regenerating the response files.
        (The `tag` has to be unique.)
        """
        releases_before = self.hello_world_project.get_releases()
        latest_release = releases_before[0].tag_name
        count_before = len(releases_before)
        increased_release = ".".join(
            [
                latest_release.rsplit(".", 1)[0],
                str(int(latest_release.rsplit(".", 1)[1]) + 1),
            ]
        )
        release = self.hello_world_project.create_release(
            tag=increased_release, name="test", message="testing release"
        )
        count_after = len(self.hello_world_project.get_releases())
        assert release.tag_name == increased_release
        assert release.title == "test"
        assert release.body == "testing release"
        assert count_before + 1 == count_after

    def test_edit_release(self):
        release = self.hello_world_project.get_release(tag_name="0.1.0")
        origin_name = release.title
        origin_message = release.body

        release.edit_release(
            name=f"{origin_name}-changed", message=f"{origin_message}-changed"
        )
        assert release.title == f"{origin_name}-changed"
        assert release.body == f"{origin_message}-changed"

    def test_latest_release(self):
        last_version = "0.7.0"
        release = self.ogr_project.get_latest_release()
        assert release.tag_name == last_version
        assert release.title == last_version
        assert "New Features" in release.body


class Forks(GithubTests):
    def test_fork(self):
        assert self.ogr_fork.is_fork is True
        fork_description = self.ogr_fork.get_description()
        assert fork_description

    @unittest.skip(
        "not working with yaml file because it  check exception within setup"
    )
    def test_nonexisting_fork(self):
        self.ogr_nonexisting_fork = self.service.get_project(
            repo="omfeprkfmwpefmwpefkmwpeofjwepof", is_fork=True
        )
        with self.assertRaises(GithubException) as ex:
            self.ogr_nonexisting_fork.get_description()
        s = str(ex.value.args)
        assert "Not Found" in s
        assert "404" in s

    def test_get_fork(self):
        fork = self.ogr_project.get_fork()
        assert fork
        assert fork.get_description()

    def test_is_fork(self):
        assert not self.ogr_project.is_fork
        is_forked = self.ogr_project.is_forked()
        assert isinstance(is_forked, bool)
        # `is True` is here on purpose: we want to be sure that .is_forked() returns True object
        # because Tomas had his crazy ideas and wanted to return GitProject directly,
        # stop that madman
        assert is_forked is True
        fork = self.ogr_project.get_fork(create=False)
        assert fork
        assert fork.is_fork

    def test_create_fork(self):
        """
        Remove your fork https://github.com/$USERNAME/fed-to-brew
        before regenerating the response files.
        """
        not_existing_fork = self.not_forked_project.get_fork(create=False)
        assert not not_existing_fork
        assert not self.not_forked_project.is_forked()

        old_forks = self.not_forked_project.service.user.get_forks()

        self.not_forked_project.fork_create()

        assert self.not_forked_project.get_fork().get_description()
        assert self.not_forked_project.is_forked()

        new_forks = self.not_forked_project.service.user.get_forks()
        assert len(old_forks) == len(new_forks) - 1


class Service(GithubTests):
    def test_project_create(self):
        """
        Remove https://github.com/$USERNAME/repo_created_for_test repository before regeneration

        """
        name_of_the_repo = "repo_created_for_test"
        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        with self.assertRaises(UnknownObjectException):
            project.github_repo

        new_project = self.service.project_create(name_of_the_repo)
        assert new_project.repo == name_of_the_repo
        assert new_project.github_repo

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        assert project.github_repo

    def test_project_create_in_the_group(self):
        """
        Remove https://github.com/packit-service/repo_created_for_test_in_group
        repository before regeneration
        """
        name_of_the_repo = "repo_created_for_test_in_group"
        namespace_of_the_repo = "packit-service"
        project = self.service.get_project(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        with self.assertRaises(UnknownObjectException):
            project.github_repo

        new_project = self.service.project_create(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        assert new_project.repo == name_of_the_repo
        assert new_project.namespace == namespace_of_the_repo
        assert new_project.github_repo

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        assert project.github_repo

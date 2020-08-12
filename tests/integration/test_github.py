import os
import unittest
from datetime import datetime

import pytest
from github import GithubException, UnknownObjectException
from requre import RequreTestCase
from requre.storage import PersistentObjectStorage
from requre.utils import StorageMode

from ogr import GithubService
from ogr.abstract import PRStatus, IssueStatus, CommitStatus, AccessLevel
from ogr.exceptions import GithubAPIException


class GithubTests(RequreTestCase):
    def setUp(self):
        super().setUp()
        self.token = os.environ.get("GITHUB_TOKEN")
        if PersistentObjectStorage().mode == StorageMode.write and (not self.token):
            raise EnvironmentError(
                "You are in Requre write mode, please set proper GITHUB_TOKEN env variables"
            )

        self.service = GithubService(token=self.token)
        self._ogr_project = None
        self._ogr_fork = None
        self._hello_world_project = None
        self._not_forked_project = None

    @property
    def ogr_project(self):
        if not self._ogr_project:
            self._ogr_project = self.service.get_project(namespace="packit", repo="ogr")
        return self._ogr_project

    @property
    def ogr_fork(self):
        if not self._ogr_fork:
            self._ogr_fork = self.service.get_project(
                namespace="packit", repo="ogr", is_fork=True
            )
        return self._ogr_fork

    @property
    def hello_world_project(self):
        if not self._hello_world_project:
            self._hello_world_project = self.service.get_project(
                namespace="packit", repo="hello-world"
            )
        return self._hello_world_project

    @property
    def not_forked_project(self):
        if not self._not_forked_project:
            self._not_forked_project = self.service.get_project(
                namespace="fedora-modularity", repo="fed-to-brew"
            )
        return self._not_forked_project


class Comments(GithubTests):
    def test_pr_comments(self):
        pr_comments = self.ogr_project.get_pr_comments(9)
        assert pr_comments
        assert len(pr_comments) == 2

        assert pr_comments[0].body.endswith("fixed")
        assert pr_comments[1].body.startswith("LGTM")

    def test_pr_comments_reversed(self):
        pr_comments = self.ogr_project.get_pr_comments(9, reverse=True)
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[0].body.startswith("LGTM")

    def test_pr_comments_filter(self):
        pr_comments = self.ogr_project.get_pr_comments(9, filter_regex="fixed")
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].body.startswith("@TomasTomecek")

        pr_comments = self.ogr_project.get_pr_comments(
            9, filter_regex="LGTM, nicely ([a-z]*)"
        )
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].body.endswith("done!")

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
        assert comments[0].body.startswith("/packit")

    def test_issue_comments_reversed(self):
        comments = self.ogr_project.get_issue_comments(194, reverse=True)
        assert len(comments) == 6
        assert comments[0].body.startswith("The ")

    def test_issue_comments_regex(self):
        comments = self.ogr_project.get_issue_comments(
            194, filter_regex=r".*Fedora package.*"
        )
        assert len(comments) == 3
        assert "master" in comments[0].body

    def test_issue_comments_regex_reversed(self):
        comments = self.ogr_project.get_issue_comments(
            194, reverse=True, filter_regex=".*Fedora package.*"
        )
        assert len(comments) == 3
        assert "f29" in comments[0].body

    def test_pr_comments_author_regex(self):
        comments = self.ogr_project.get_pr_comments(
            217, filter_regex="^I", author="mfocko"
        )
        assert len(comments) == 1
        assert "API" in comments[0].body

    def test_pr_comments_author(self):
        comments = self.ogr_project.get_pr_comments(217, author="lachmanfrantisek")
        assert len(comments) == 3
        assert comments[0].body.endswith("here.")

    def test_issue_comments_author_regex(self):
        comments = self.ogr_project.get_issue_comments(
            220, filter_regex=".*API.*", author="lachmanfrantisek"
        )
        assert len(comments) == 1
        assert comments[0].body.startswith("After")

    def test_issue_comments_author(self):
        comments = self.ogr_project.get_issue_comments(220, author="mfocko")
        assert len(comments) == 2
        assert comments[0].body.startswith("What")
        assert comments[1].body.startswith("Consider")

    def test_issue_comments_updates(self):
        comments = self.hello_world_project.get_issue_comments(
            61, filter_regex="comment-update"
        )
        assert len(comments) == 1
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "see if updating works"
        assert comments[0].body == "see if updating works"
        assert comments[0].edited > before_edited

        comments[0].body = before_comment
        assert comments[0].body == before_comment

    def test_pr_comments_updates(self):
        comments = self.hello_world_project.get_pr_comments(
            72, filter_regex="comment updates"
        )
        assert len(comments) == 1
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "see if updating works"
        assert comments[0].body == "see if updating works"
        assert comments[0].edited > before_edited

        comments[0].body = before_comment
        assert comments[0].body == before_comment


class GenericCommands(GithubTests):
    def test_add_user(self):
        project = self.service.get_project(repo="clynica", namespace="Beauth")
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

        issue = self.ogr_project.get_issue_info(4)
        assert self.ogr_project.can_close_issue("lachmanfrantisek", issue)

    def test_issue_permissions_cant_close(self):
        issue = self.ogr_project.get_issue_info(4)
        assert not self.ogr_project.can_close_issue("unknown_user", issue)

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

    def test_is_not_private(self):
        # The repository bellow needs to be a private repository which can be
        # accessed by the user who's GITHUB_TOKEN is used for
        # test regeneration.
        private_project = self.service.get_project(namespace="csomh", repo="playground")
        assert private_project.is_private()

    def test_is_private(self):
        assert not self.ogr_project.is_private()


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

    def test_create_issue(self):
        title = "This is an issue"
        description = "Example of Issue description"
        labels = ["label1", "label2"]
        project = self.service.get_project(namespace="shreyaspapi", repo="test")
        issue = project.create_issue(title=title, body=description, labels=labels)
        assert issue.title == title
        assert issue.description == description
        for issue_label, label in zip(issue.labels, labels):
            assert issue_label.name == label

        with self.assertRaises(NotImplementedError):
            project.create_issue(title=title, body=description, private=True)

    def test_issue_without_label(self):
        project = self.service.get_project(namespace="shreyaspapi", repo="test")
        title = "This is an issue"
        description = "Example of Issue description"
        issue = project.create_issue(title=title, body=description)
        assert issue.title == title
        assert issue.description == description

    def test_issue_list_author(self):
        issue_list = self.ogr_project.get_issue_list(
            status=IssueStatus.all, author="mfocko"
        )
        assert issue_list
        assert len(issue_list) >= 12

    def test_issue_list_nonexisting_author(self):
        issue_list = self.ogr_project.get_issue_list(
            status=IssueStatus.all, author="xyzidontexist"
        )
        assert len(issue_list) == 0

    def test_issue_list_assignee(self):
        issue_list = self.ogr_project.get_issue_list(
            status=IssueStatus.all, assignee="mfocko"
        )
        assert issue_list
        assert len(issue_list) >= 10

    def test_issue_list_labels(self):
        issue_list = self.ogr_project.get_issue_list(
            status=IssueStatus.all, labels=["Pagure"]
        )
        assert issue_list
        assert len(issue_list) >= 42

    def test_issue_info(self):
        issue_info = self.ogr_project.get_issue_info(issue_id=4)
        assert issue_info
        assert issue_info.title.startswith("Better name")
        assert issue_info.status == IssueStatus.closed

    def test_issue_labels(self):
        """
        Remove the labels from this issue before regenerating the response files:
        https://github.com/packit/ogr/issues/4
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

    def test_issue_updates(self):
        issue = self.hello_world_project.get_issue(issue_id=61)
        old_comments = issue.get_comments()
        issue.comment("test comment")
        new_comments = issue.get_comments()
        assert len(new_comments) > len(old_comments)

    def test_setters(self):
        issue = self.hello_world_project.get_issue(issue_id=61)

        old_title = issue.title
        issue.title = "test title"
        assert issue.title != old_title
        assert issue.title == "test title"

        issue.title = old_title
        assert issue.title == old_title

        old_description = issue.description
        issue.description = "test description"
        assert issue.description != old_description
        assert issue.description == "test description"

        issue.description = old_description
        assert issue.description == old_description


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
        assert pr_info.author == "lachmanfrantisek"
        assert pr_info.url == "https://github.com/packit/ogr/pull/1"
        assert pr_info.diff_url == "https://github.com/packit/ogr/pull/1/files"

    def test_all_pr_commits(self):
        commits = self.ogr_project.get_all_pr_commits(pr_id=1)
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

    def test_pr_create_fork_other_fork(self):
        fork_project = self.service.get_project(namespace="mfocko", repo="hello-world")
        other_fork_project = self.service.get_project(
            namespace="lachmanfrantisek", repo="hello-world"
        )
        pr_opened_before = len(other_fork_project.get_pr_list(status=PRStatus.open))
        opened_pr = fork_project.pr_create(
            title="test: other_fork(master) <- fork",
            body="pull request body",
            target_branch="master",
            source_branch="test_source",
            fork_username="lachmanfrantisek",
        )
        pr_opened_after = len(other_fork_project.get_pr_list(status=PRStatus.open))
        other_fork_project.pr_close(opened_pr.id)

        assert opened_pr.title == "test: other_fork(master) <- fork"
        assert opened_pr.status == PRStatus.open
        assert pr_opened_after == pr_opened_before + 1

    def test_pr_labels(self):
        """
        Remove the labels from this pr before regenerating the response files:
        https://github.com/packit/ogr/pull/1
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
        pr = self.hello_world_project.get_pr(72)
        source_project = pr.source_project
        # The namespace was 'packit-service' when this PR was opened.
        assert source_project.namespace == "packit-service"
        assert source_project.repo == "hello-world"

    def test_source_project_upstream_fork(self):
        pr = self.hello_world_project.get_pr(111)
        source_project = pr.source_project
        assert source_project.namespace == "lbarcziova"
        assert source_project.repo == "hello-world"

    def test_source_project_fork_fork(self):
        project = self.service.get_project(repo="hello-world", namespace="mfocko")
        pr = project.get_pr(1)
        source_project = pr.source_project
        assert source_project.namespace == "mfocko"
        assert source_project.repo == "hello-world"

    def test_source_project_other_fork_fork(self):
        project = self.service.get_project(
            repo="hello-world", namespace="lachmanfrantisek"
        )
        pr = project.get_pr(1)
        source_project = pr.source_project
        assert source_project.namespace == "mfocko"
        assert source_project.repo == "hello-world"

    def test_source_project_renamed_fork(self):
        pr = self.hello_world_project.get_pr(113)
        source_project = pr.source_project
        assert source_project.namespace == "mfocko"
        assert source_project.repo == "bye-world"

    def test_source_project_renamed_upstream(self):
        pr = self.service.get_project(
            repo="not-potential-spoon", namespace="packit"
        ).get_pr(1)
        source_project = pr.source_project
        assert source_project.namespace == "mfocko"
        assert source_project.repo == "potential-spoon"


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

    @unittest.skip("not working with yaml file because it check exception within setup")
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

        forked_project = self.not_forked_project.fork_create()
        assert (
            forked_project.namespace == forked_project.github_instance.get_user().login
        )
        assert forked_project.repo == "fed-to-brew"

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
        Remove https://github.com/packit/repo_created_for_test_in_group
        repository before regeneration
        """
        name_of_the_repo = "repo_created_for_test_in_group"
        namespace_of_the_repo = "packit"
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

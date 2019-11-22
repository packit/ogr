import os
import unittest

import pytest
from gitlab import GitlabGetError

from ogr.exceptions import GitlabAPIException
from requre.storage import PersistentObjectStorage
from ogr.abstract import PRStatus, IssueStatus
from ogr.services.gitlab import GitlabService

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class GitlabTests(unittest.TestCase):
    def setUp(self):
        self.token = os.environ.get("GITLAB_TOKEN")
        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_gitlab_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file

        if PersistentObjectStorage().is_write_mode and not self.token:
            raise EnvironmentError("please set GITLAB_TOKEN env variables")
        elif not self.token:
            self.token = "some_token"

        self.service = GitlabService(
            token=self.token, instance_url="https://gitlab.com", ssl_verify=True
        )

        self.project = self.service.get_project(
            repo="ogr-tests", namespace="packit-service"
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
        assert "Testing repository for python-ogr package." in file_content

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

    def test_get_description(self):
        description = self.project.get_description()
        assert description
        assert description.startswith("Testing repository for python-ogr package.")

    def test_get_git_urls(self):
        urls = self.project.get_git_urls()
        assert urls
        assert len(urls) == 2
        assert "git" in urls
        assert "ssh" in urls
        assert urls["git"] == "https://gitlab.com/packit-service/ogr-tests.git"
        assert urls["ssh"].endswith("git@gitlab.com:packit-service/ogr-tests.git")

    def test_get_sha_from_tag(self):
        assert (
            self.project.get_sha_from_tag("0.1.0")
            == "24c86d0704694f686329b2ea636c5b7522cfdc40"
        )
        with pytest.raises(GitlabAPIException) as ex:
            self.project.get_sha_from_tag("future")
        assert "not found" in str(ex.value)

    def test_parent_project(self):
        assert self.project.get_fork().parent.namespace == "packit-service"
        assert self.project.get_fork().parent.repo == "ogr-tests"

    def test_get_commit_statuses(self):
        flags = self.project.get_commit_statuses(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64"
        )
        assert isinstance(flags, list)
        assert len(flags) >= 2
        assert flags[0].state == "success"
        assert flags[0].comment == "testing status"
        assert flags[0].context == "default"

    def test_set_commit_status(self):
        old_statuses = self.project.get_commit_statuses(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64"
        )
        status = self.project.set_commit_status(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
            state="success",
            target_url="https://gitlab.com/packit-service/ogr-tests",
            description="testing status",
            context="test",
        )
        assert status
        new_statuses = self.project.get_commit_statuses(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64"
        )
        assert len(old_statuses) == len(new_statuses)

    def test_commit_comment(self):
        comment = self.project.commit_comment(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
            body="Comment to line 3",
            filename="README.md",
            row=3,
        )
        assert comment.author == self.service.user.get_username()
        assert comment.comment == "Comment to line 3"

    def test_get_web_url(self):
        url = self.project.get_web_url()
        assert url == "https://gitlab.com/packit-service/ogr-tests"

    def test_full_repo_name(self):
        assert self.project.full_repo_name == "packit-service/ogr-tests"

    def test_get_owners(self):
        owners = self.project.get_owners()
        assert set(("lachmanfrantisek", "lbarcziova")).issubset(set(owners))

    def test_issue_permissions(self):
        users = self.project.who_can_close_issue()
        assert "lachmanfrantisek" in users
        assert "lbarcziova" in users

        issue = self.project.get_issue_info(1)
        assert self.project.can_close_issue("lachmanfrantisek", issue)
        assert not self.project.can_close_issue("not_existing_user", issue)

    def test_pr_permissions(self):
        users = self.project.who_can_merge_pr()
        assert "lachmanfrantisek" in users
        assert "lbarcziova" in users

        assert self.project.can_merge_pr("lachmanfrantisek")
        assert not self.project.can_merge_pr("not_existing_user")


class Issues(GitlabTests):
    """
    Add another random string for creating merge requests,
    otherwise gitlab will report you are SPAMMING
    """

    random_str = "abcde"

    def test_get_issue_list(self):
        issue_list = self.project.get_issue_list()
        assert issue_list
        assert len(issue_list) >= 1

    def test_issue_info(self):
        issue_info = self.project.get_issue_info(issue_id=1)
        assert issue_info
        assert issue_info.title.startswith("My first issue")
        assert issue_info.description.startswith("This is testing issue")

    def test_create_issue(self):
        """
        see class comment in case of fail
        """
        issue_title = f"New Issue {self.random_str}"
        issue_desc = f"Description for issue {self.random_str}"
        issue = self.project.create_issue(title=issue_title, description=issue_desc)
        assert issue.title == issue_title
        assert issue.description == issue_desc

    def test_close_issue(self):
        """
        see class comment in case of fail
        """
        issue = self.project.create_issue(
            title=f"Close issue {self.random_str}",
            description=f"Description for issue for closing {self.random_str}",
        )
        issue_for_closing = self.project.get_issue_info(issue_id=issue.id)
        assert issue_for_closing.status == IssueStatus.open
        issue = self.project.issue_close(issue_id=issue.id)
        assert issue.status == IssueStatus.closed

    def test_get_issue_comments(self):
        comments = self.project.get_issue_comments(issue_id=2)
        assert len(comments) == 5
        assert comments[0].comment.startswith("Comment")
        assert comments[0].author == "lbarcziova"

    def test_get_issue_comments_reversed(self):
        comments = self.project.get_issue_comments(issue_id=2, reverse=True)
        assert len(comments) == 5
        assert comments[0].comment.startswith("regex")

    def test_get_issue_comments_regex(self):
        comments = self.project.get_issue_comments(issue_id=2, filter_regex="regex")
        assert len(comments) == 2
        assert comments[0].comment.startswith("let's")

    def test_get_issue_comments_regex_reversed(self):
        comments = self.project.get_issue_comments(
            issue_id=2, filter_regex="regex", reverse=True
        )
        assert len(comments) == 2
        assert comments[0].comment.startswith("regex")

    def test_issue_labels(self):
        """
        Remove labels before regenerating:
        https://gitlab.com/packit-service/ogr-tests/issues/1
        """
        labels = self.project.get_issue_labels(issue_id=1)

        assert not labels
        self.project.add_issue_labels(issue_id=1, labels=["test_lb1", "test_lb2"])
        labels = self.project.get_issue_labels(issue_id=1)
        assert len(labels) == 2
        assert labels[0] == "test_lb1"
        assert labels[1] == "test_lb2"

    def test_get_issue_comments_author_regex(self):
        comments = self.project.get_issue_comments(
            issue_id=2, filter_regex="2$", author="lbarcziova"
        )
        assert len(comments) == 1
        assert comments[0].comment.startswith("Comment")

    def test_get_issue_comments_author(self):
        comments = self.project.get_issue_comments(issue_id=2, author="mfocko")
        assert len(comments) == 2
        assert comments[0].comment.startswith("let's")
        assert comments[1].comment.startswith("regex")


class PullRequests(GitlabTests):
    def test_pr_list(self):
        title = "some special title"
        pr = self.create_pull_request(title=title)
        pr_list = self.project.get_pr_list()
        count = len(pr_list)
        assert count >= 1
        assert title == pr_list[0].title
        self.project.pr_close(pr_id=pr.id)

    def test_pr_info(self):
        pr_info = self.project.get_pr_info(pr_id=1)
        assert pr_info
        assert pr_info.title == "change"
        assert pr_info.description == "description of mergerequest"
        assert (
            pr_info.url
            == "https://gitlab.com/packit-service/ogr-tests/merge_requests/1"
        )
        assert (
            pr_info.diff_url
            == "https://gitlab.com/packit-service/ogr-tests/merge_requests/1/diffs"
        )

    def test_get_all_pr_commits(self):
        commits = self.project.get_all_pr_commits(pr_id=1)
        assert commits[0] == "d490ec67dd98f69dfdc1732b98bb3189f0e0aace"
        assert commits[1] == "3c1fb11dd358254cc3f1588f173e54e98c1d4c09"
        assert len(commits) == 2

    def test_get_all_pr_comments(self):
        comments = self.project._get_all_pr_comments(pr_id=1)
        count = len(comments)
        assert comments[0].comment == "first comment of mergerequest"
        assert comments[0].author == "lbarcziova"
        assert count >= 2

    def test_update_pr_info(self):
        pr_info = self.project.get_pr_info(pr_id=1)
        original_description = pr_info.description

        self.project.update_pr_info(pr_id=1, description="changed description")
        pr_info = self.project.get_pr_info(pr_id=1)
        assert pr_info.description == "changed description"

        self.project.update_pr_info(pr_id=1, description=original_description)
        pr_info = self.project.get_pr_info(pr_id=1)
        assert pr_info.description == original_description

    def create_pull_request(
        self, title="New PR of pr-3", body="Description", dest="master", source="pr-3"
    ):
        return self.project.pr_create(title, body, dest, source)

    def test_pr_close(self):
        pr = self.create_pull_request()
        pr_for_closing = self.project.get_pr_info(pr_id=pr.id)
        assert pr_for_closing.status == PRStatus.open
        closed_pr = self.project.pr_close(pr_id=pr.id)
        assert closed_pr.status == PRStatus.closed

    def test_pr_merge(self):
        """
        Create new PR and update pull request ID to this test before this test
        """
        pull_request_id = 17
        pr_for_merging = self.project.get_pr_info(pr_id=pull_request_id)
        assert pr_for_merging.status == PRStatus.open
        merged_pr = self.project.pr_merge(pr_id=pull_request_id)
        assert merged_pr.status == PRStatus.merged

    def test_pr_labels(self):
        """
        Remove labels before regenerating:
        https://gitlab.com/packit-service/ogr-tests/merge_requests/1
        """
        labels = self.project.get_pr_labels(pr_id=1)
        assert not labels
        self.project.add_pr_labels(pr_id=1, labels=["test_lb1", "test_lb2"])
        labels = self.project.get_pr_labels(pr_id=1)
        assert len(labels) == 2
        assert labels[0] == "test_lb1"
        assert labels[1] == "test_lb2"

    def test_get_pr_comments_author_regex(self):
        comments = self.project.get_pr_comments(
            pr_id=1, filter_regex="test$", author="mfocko"
        )
        assert len(comments) == 1
        assert comments[0].comment.startswith("author")

    def test_get_pr_comments_author(self):
        comments = self.project.get_pr_comments(pr_id=1, author="mfocko")
        assert len(comments) == 2
        assert comments[0].comment.startswith("second")


class Tags(GitlabTests):
    def test_get_tags(self):
        tags = self.project.get_tags()
        count = len(tags)
        assert count >= 2
        assert tags[count - 1].name == "0.1.0"
        assert tags[count - 1].commit_sha == "24c86d0704694f686329b2ea636c5b7522cfdc40"

    def test_tag_from_tag_name(self):
        tag = self.project._git_tag_from_tag_name(tag_name="0.1.0")
        assert tag.commit_sha == "24c86d0704694f686329b2ea636c5b7522cfdc40"


class Releases(GitlabTests):
    def test_create_release(self):
        releases_before = self.project.get_releases()
        version_list = releases_before[0].tag_name.rsplit(".", 1)
        increased = ".".join([version_list[0], str(int(version_list[1]) + 1)])
        count_before = len(releases_before)
        release = self.project.create_release(
            name=f"test {increased}",
            tag_name=increased,
            description=f"testing release-{increased}",
            ref="master",
        )
        count_after = len(self.project.get_releases())
        assert release.tag_name == increased
        assert release.title == f"test {increased}"
        assert release.body == f"testing release-{increased}"
        assert count_before + 1 == count_after

    def test_get_releases(self):
        releases = self.project.get_releases()
        assert releases
        count = len(releases)
        assert count >= 1
        assert releases[-1].title == "test"
        assert releases[-1].tag_name == "0.1.0"
        assert releases[-1].body == "testing release"

    def test_get_latest_release(self):
        release = self.project.get_releases()[0]
        latest_release = self.project.get_latest_release()
        assert latest_release.title == release.title
        assert latest_release.tag_name == release.tag_name
        assert latest_release.body == release.body


class Service(GitlabTests):
    def test_project_create(self):
        """
        Remove https://gitlab.com/$USERNAME/new-ogr-testing-repo before data regeneration
        """
        name_of_the_repo = "new-ogr-testing-repo"
        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        with pytest.raises(GitlabGetError):
            assert project.gitlab_repo

        new_project = self.service.project_create(name_of_the_repo)
        assert new_project.repo == name_of_the_repo
        assert new_project.gitlab_repo

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=self.service.user.get_username()
        )
        assert project.gitlab_repo

    def test_project_create_in_the_group(self):
        """
        Remove https://gitlab.com/packit-service/new-ogr-testing-repo-in-the-group
        before data regeneration.
        """
        name_of_the_repo = "new-ogr-testing-repo-in-the-group"
        namespace_of_the_repo = "packit-service"
        project = self.service.get_project(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        with pytest.raises(GitlabGetError):
            assert project.gitlab_repo

        new_project = self.service.project_create(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        assert new_project.repo == name_of_the_repo
        assert new_project.namespace == namespace_of_the_repo
        assert new_project.gitlab_repo

        project = self.service.get_project(
            repo=name_of_the_repo, namespace=namespace_of_the_repo
        )
        assert project.gitlab_repo


class Forks(GitlabTests):
    def test_get_fork(self):
        fork = self.project.get_fork()
        assert fork
        assert fork.get_description()

    def test_is_fork(self):
        assert not self.project.is_fork
        assert self.project.is_forked()
        fork = self.project.get_fork(create=False)
        assert fork
        assert fork.is_fork

    def test_create_fork(self):
        """
        Remove https://gitlab.com/$USERNAME/ogr-tests before data regeneration
        """
        not_existing_fork = self.project.get_fork(create=False)
        assert not not_existing_fork
        assert not self.project.is_forked()

        new_fork = self.project.fork_create()

        assert self.project.get_fork()
        assert self.project.is_forked()
        assert new_fork.is_fork

import os
from datetime import datetime

import pytest
from requre.utils import get_datafile_filename
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.pagure.base import PagureTests
from ogr import PagureService
from ogr.abstract import IssueStatus, CommitStatus
from ogr.exceptions import PagureAPIException


@record_requests_for_all_methods()
class PagureProjectTokenCommands(PagureTests):
    def setUp(self):
        super().setUp()
        self.token = os.environ.get("PAGURE_OGR_TEST_TOKEN", "")

        if not get_datafile_filename(obj=self) and (not self.token):
            raise EnvironmentError("please set PAGURE_OGR_TEST_TOKEN env variables")

        self._service = None
        self._user = None
        self._ogr_project = None
        self._ogr_fork = None

    @property
    def service(self):
        if not self._service:
            self._service = PagureService(
                token=self.token, instance_url="https://pagure.io"
            )
        return self._service

    def test_issue_permissions(self):
        owners = self.ogr_project.who_can_close_issue()
        assert "lachmanfrantisek" in owners

        issue = self.ogr_project.get_issue(2)
        assert issue.can_close("lachmanfrantisek")

    def test_issue_comments(self):
        issue_comments = self.ogr_project.get_issue(3)._get_all_comments()
        assert issue_comments
        assert len(issue_comments) == 4
        assert issue_comments[0].body.startswith("test")
        assert issue_comments[1].body.startswith("tests")

    def test_issue_info(self):
        issue_info = self.ogr_project.get_issue(issue_id=2)
        assert issue_info
        assert issue_info.title.startswith("Test 1")
        assert issue_info.status == IssueStatus.closed

    def test_issue_comments_reversed(self):
        issue_comments = self.ogr_project.get_issue(3).get_comments(reverse=True)
        assert len(issue_comments) == 4
        assert issue_comments[0].body.startswith("regex")

    def test_issue_comments_regex(self):
        issue_comments = self.ogr_project.get_issue(3).get_comments(
            filter_regex="regex"
        )
        assert len(issue_comments) == 2
        assert issue_comments[0].body.startswith("let's")

    def test_issue_comments_regex_reversed(self):
        issue_comments = self.ogr_project.get_issue(3).get_comments(
            filter_regex="regex", reverse=True
        )
        assert len(issue_comments) == 2
        assert issue_comments[0].body.startswith("regex")

    def test_issue_update_title(self):
        issue = self.ogr_project.get_issue(3)
        old_title, old_description = issue.title, issue.description

        issue.title = "testing title"
        assert (issue.title, issue.description) == ("testing title", old_description)

        issue.title = old_title
        assert (issue.title, issue.description) == (old_title, old_description)

    def test_issue_update_description(self):
        issue = self.ogr_project.get_issue(3)
        old_title, old_description = issue.title, issue.description

        issue.description = "testing description"
        assert (issue.title, issue.description) == (old_title, "testing description")

        issue.description = old_description
        assert (issue.title, issue.description) == (old_title, old_description)

    def test_update_pr_info(self):
        pr_info = self.ogr_project.get_pr(pr_id=4)
        orig_title = pr_info.title
        orig_description = pr_info.description

        self.ogr_project.get_pr(4).update_info(
            title="changed", description="changed description"
        )
        pr_info = self.ogr_project.get_pr(pr_id=4)
        assert pr_info.title == "changed"
        assert pr_info.description == "changed description"

        self.ogr_project.get_pr(4).update_info(
            title=orig_title, description=orig_description
        )
        pr_info = self.ogr_project.get_pr(pr_id=4)
        assert pr_info.title == orig_title
        assert pr_info.description == orig_description

    def test_pr_setters(self):
        pr = self.ogr_project.get_pr(pr_id=6)

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

    def test_pr_comments_author_regex(self):
        comments = self.ogr_project.get_pr(4).get_comments(
            filter_regex="^regex", author="mfocko"
        )
        assert len(comments) == 1
        assert comments[0].body.endswith("test")

    def test_pr_comments_author(self):
        comments = self.ogr_project.get_pr(4).get_comments(author="lachmanfrantisek")
        assert len(comments) == 0

    def test_issue_comments_author_regex(self):
        comments = self.ogr_project.get_issue(3).get_comments(
            filter_regex="^test[s]?$", author="mfocko"
        )
        assert len(comments) == 2
        assert comments[0].body == "test"
        assert comments[1].body == "tests"

    def test_issue_comments_author(self):
        comments = self.ogr_project.get_issue(3).get_comments(author="lachmanfrantisek")
        assert len(comments) == 0

    def test_pr_status(self):
        pr = self.ogr_project.get_pr(pr_id=4)
        self.ogr_project.set_commit_status(
            commit=pr.head_commit,
            state=CommitStatus.success,
            target_url="https://pagure.io/ogr-tests/pull-request/4",
            description="not failed test",
            context="test",
        )

        statuses = pr.get_statuses()
        assert statuses
        assert len(statuses) >= 0
        assert statuses[-1].state == CommitStatus.success
        assert statuses[-1].created >= datetime(
            year=2020,
            month=8,
            day=31,
            hour=7,
            minute=0,
            second=0,
        )
        assert statuses[-1].edited >= datetime(
            year=2020, month=8, day=31, hour=9, minute=36, second=50
        )

    def test_is_private(self):
        self.service.instance_url = "https://src.fedoraproject.org"
        assert not self.ogr_project.is_private()

    def test_token_is_none_then_set(self):
        token = self.service._token
        self.service.change_token("")
        try:
            with pytest.raises(PagureAPIException) as exc:
                self.service.user.get_username()
            assert "Invalid or expired token" in str(exc)
        finally:
            self.service.change_token(token)

        self.service.user.get_username()
        self.service.user.get_username()  # 2nd identical call

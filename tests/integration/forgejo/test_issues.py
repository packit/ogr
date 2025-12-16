# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest
from requre.helpers import record_httpx
from requre.online_replacing import record_requests_for_all_methods

from ogr.abstract import IssueStatus
from ogr.exceptions import (
    ForgejoAPIException,
    GitForgeInternalError,
    IssueTrackerDisabled,
)
from tests.integration.forgejo.base import ForgejoTests


@record_httpx()
@record_requests_for_all_methods()
class Issues(ForgejoTests):

    random_str = "abcdedfgh"
    title = "Issue title"
    description = "Issue body"

    def test_get_issue_list(self):
        issue_list = self.project.get_issue_list()
        assert issue_list
        assert len(issue_list) >= 1

    def test_get_issue_list_author(self):
        issue_list = self.project.get_issue_list(
            status=IssueStatus.all,
            author="packit-validator",
        )
        assert issue_list
        assert len(issue_list) >= 3

    def test_get_issue_list_nonexisting_author(self):
        with pytest.raises(ForgejoAPIException):
            self.project.get_issue_list(
                status=IssueStatus.all,
                author="xyzidontexist",
            )

    def test_get_issue_list_assignee(self):
        issue_list = self.project.get_issue_list(
            status=IssueStatus.all,
            assignee="packit-validator",
        )
        assert issue_list
        assert len(issue_list) >= 1

    def test_issue_info(self):
        title = "test Title ABC"
        description = "This is a test issue for checking title prefix"
        issue = self.project.create_issue(title=title, body=description)
        fetched = self.project.get_issue(issue.id)
        assert fetched.title.startswith("test Title")

    def test_create_issue_with_assignee(self):
        issue_title = "This is a example issue"
        issue_desc = "Description for issue"
        assign = ["packit-validator"]
        project = self.project
        issue = project.create_issue(
            title=issue_title,
            body=issue_desc,
            assignees=assign,
        )
        assert issue.title == issue_title
        assert issue.assignees[0].login == assign[0]
        assert issue.description == issue_desc

    def test_create_issue_with_labels(self):
        issue_title = "A super duper issue"
        issue_desc = "Description for issue"

        # labels need to be sorted alphabetically as that is the order
        # in which they are returned by the API
        labels = ["b", "label2"]

        issue = self.project.create_issue(
            title=issue_title,
            body=issue_desc,
            labels=labels,
        )
        assert issue.title == issue_title
        assert issue.description == issue_desc
        assert issue.labels

        for issue_label, label in zip(issue.labels, labels):
            assert issue_label.name == label

    def test_close_issue(self):
        issue = self.project.create_issue(
            title=f"Close issue {self.random_str}",
            body=f"Description for issue for closing {self.random_str}",
        )
        issue_for_closing = self.project.get_issue(issue_id=issue.id)
        assert issue_for_closing.status == IssueStatus.open

        issue.close()
        assert issue.status == IssueStatus.closed

    def test_issue_assignees(self):
        project = self.project
        assignees = project.get_issue(223).assignees
        assert len(assignees) == 1
        assert assignees[0].login == "packit-validator"

    def test_issue_updates(self):
        issue = self.project.get_issue(issue_id=224)
        old_comments = list(issue.get_comments())
        issue.comment("test comment")
        new_comments = list(issue.get_comments())
        assert len(new_comments) > len(old_comments)

    def test_issue_labels(self):
        """
        Remove the labels from this issue before regenerating the response files:
        https://v10.next.forgejo.org/packit-validator/ogr-tests/issues/224
        """
        issue = self.project.get_issue(224)
        labels = issue.labels

        assert not labels
        issue.add_label("test_lb1", "test_lb2")
        labels = self.project.get_issue(224).labels
        assert labels
        assert next(iter(labels)).name == "test_lb1"

    def test_issue_add_assignee(self):
        """
        Remove the assignees from this issue before regenerating the response files:
        https://v10.next.forgejo.org/packit-validator/ogr-tests/issues/245
        """
        issue = self.project.get_issue(245)
        print(self.service.user.get_username())
        assignees = issue.assignees

        assert not assignees
        issue.add_assignee("packit-validator")
        assignees = self.project.get_issue(245).assignees
        assert len(assignees) == 1
        assert assignees[0].login == "packit-validator"

    def test_issue_add_assignee_without_redundant_api_call(self):
        """
        Remove the assignees from this issue before regenerating the response files:
        https://v10.next.forgejo.org/packit-validator/ogr-tests/issues/245
        """
        issue = self.project.get_issue(245)
        print(self.service.user.get_username())
        assignees = issue.assignees

        assert not assignees
        issue.add_assignee("packit-validator")
        assignees = issue.assignees
        assert len(assignees) == 1
        assert assignees[0].login == "packit-validator"

    def test_issue_no_such_assignee(self):
        issue = self.project.get_issue(245)

        # __check_for_internal_failure replaces ForgejoAPIException with GitForgeInternalError
        with pytest.raises(GitForgeInternalError):
            issue.add_assignee("nonexistentuser")

    def test_list_contains_only_issues(self):
        issue_list_all = self.project.get_issue_list(status=IssueStatus.all)
        issue_ids = [issue.id for issue in issue_list_all]

        pr_ids = [143, 170, 194, 195, 198, 199, 204, 209, 220, 221]
        for id in pr_ids:
            assert id not in issue_ids

    def test_issue_doesnt_exist(self):
        with pytest.raises(ForgejoAPIException):
            self.project.get_issue(10**20)

    def test_functions_fail_for_pr(self):
        with pytest.raises(ForgejoAPIException):
            self.project.get_issue(221)
        with pytest.raises(ForgejoAPIException):
            self.project.get_issue(221).comment(body="should fail")
        with pytest.raises(ForgejoAPIException):
            self.project.get_issue(221).close()
        with pytest.raises(ForgejoAPIException):
            _ = self.project.get_issue(221).labels
        with pytest.raises(ForgejoAPIException):
            self.project.get_issue(221).add_label("should fail")

    def test_setters(self):
        issue = self.project.get_issue(issue_id=245)

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

    def test_get_comment(self):
        comment = self.project.get_issue(244).get_comment(3174)
        assert comment.body == "/packit test-comment"

    def test_get_with_disabled_issues(self):
        forks = self.project.get_forks()
        fork = next(iter(forks))
        assert fork.namespace == "mfocko"

        with pytest.raises(IssueTrackerDisabled):
            fork.get_issue(issue_id=245)

    def test_get_with_id_of_pr(self):
        pr_id = 221

        # should raise an error when retrieving
        # an issue, but providing the id of a PR instead
        with pytest.raises(ForgejoAPIException):
            self.project.get_issue(pr_id)

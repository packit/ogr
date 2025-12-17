# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.helpers import record_httpx
from requre.online_replacing import record_requests_for_all_methods

from ogr.abstract import IssueStatus
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
        issue_list = self.project.get_issue_list(
            status=IssueStatus.all,
            author="xyzidontexist",
        )
        assert len(issue_list) == 0

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

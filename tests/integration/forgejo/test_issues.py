# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from ogr.abstract import IssueStatus
from tests.integration.forgejo.base import ForgejoTests


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
            author="manky201",
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
            assignee="manky201",
        )
        assert issue_list
        assert len(issue_list) >= 3

    def test_issue_info(self):
        issue_info = self.project.get_issue(1)
        assert issue_info.title.startswith("test Title")
        assert issue_info.description.startswith("Issue")

    def test_create_issue(self):
        labels = ["test_lb2", "test_lb1"]
        issue_title = "New Issue Title"
        issue_desc = "New Issue Description"
        issue = self.project.create_issue(
            title=issue_title,
            body=issue_desc,
        )
        assert issue.title == issue_title
        assert issue.description == issue_desc
        for issue_label, label in zip(issue.labels, labels):
            assert issue_label.name == label

    def test_issue_comments_updates(self):
        comments = self.project.get_issue(1).get_comments(filter_regex="comment")
        assert len(comments) >= 7
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "see if updating works"
        assert comments[0].body == "see if updating works"
        assert comments[0].edited > before_edited

        comments[0].body = before_comment
        comments[0].body = "test comment"
        assert comments[0].body == before_comment

    def test_create_issue_with_assignee(self):
        issue_title = "This is a example issue"
        issue_desc = "Description for issue"
        assign = ["manky201"]
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

    def test_get_issue_comments(self):
        comments = self.project.get_issue(1).get_comments()
        assert len(comments) >= 7
        assert comments[0].body.startswith("test")
        assert comments[0].author == "manky201"

    def test_get_issue_comments_reversed(self):
        comments = self.project.get_issue(1).get_comments(reverse=True)
        assert len(comments) >= 7
        assert comments[0].body.startswith("test")

    def test_get_issue_comments_regex(self):
        comments = self.project.get_issue(1).get_comments(filter_regex="test")
        assert len(comments) >= 0
        assert comments[0].body.startswith("test")

    def test_get_issue_comments_regex_reversed(self):
        comments = self.project.get_issue(1).get_comments(
            filter_regex="test",
            reverse=True,
        )
        assert len(comments) >= 7
        assert comments[0].body.startswith("test")

    def test_issue_labels(self):
        issue = self.project.get_issue(1)

        labels = issue.labels
        assert not labels

        issue.add_label("test_lb1", "test_lb2")
        labels = self.project.get_issue(1).labels
        assert len(labels) == 2
        assert labels[0].name == "test_lb1"
        assert labels[1].name == "test_lb2"

    def test_issue_assignees(self):
        project = self.project
        issue = project.get_issue(1)
        assignees = issue.assignees
        assert not assignees
        issue.add_assignee("manky201")
        assignees = project.get_issue(1).assignees
        assert len(assignees) == 1
        assert assignees[0].login == "manky201"

    def test_issue_list_labels(self):
        issue_list = self.project.get_issue_list(
            status=IssueStatus.all,
            labels=["testing-label-for-test-issue-list-labels"],
        )
        assert issue_list

    def test_get_issue_comments_author_regex(self):
        comments = self.project.get_issue(1).get_comments(
            filter_regex="test",
            author="manky201",
        )
        assert len(comments) >= 1
        assert comments[0].body.startswith("test")

    def test_get_issue_comments_author(self):
        comments = self.project.get_issue(1).get_comments(author="manky201")
        assert len(comments) >= 2
        assert comments[0].body.startswith("test")
        assert comments[1].body.startswith("test")

    def test_issue_updates(self):
        issue = self.project.get_issue(issue_id=1)
        old_comments = issue.get_comments()
        issue.comment("test comment")
        new_comments = issue.get_comments()
        assert len(new_comments) > len(old_comments)

    def test_setters(self):
        issue = self.project.get_issue(issue_id=1)

        old_title = issue.title
        issue.title = "New Title"
        assert issue.title != old_title
        assert issue.title == "New Title"

        issue.title = old_title
        assert issue.title == old_title

        old_description = issue.description
        issue.description = "test description"
        assert issue.description != old_description
        assert issue.description == "test description"

        issue.description = old_description
        assert issue.description == old_description

    def test_get_comment(self):
        issue = self.project.get_issue(1)
        comment = issue.get_comment(1794)
        assert comment.body == "test comment"

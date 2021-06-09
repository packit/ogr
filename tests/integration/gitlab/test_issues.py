from requre.online_replacing import record_requests_for_all_methods

from tests.integration.gitlab.base import GitlabTests
from ogr.abstract import IssueStatus


@record_requests_for_all_methods()
class Issues(GitlabTests):
    """
    Add another random string for creating merge requests,
    otherwise gitlab will report you are SPAMMING
    """

    random_str = "abcdefghi"

    def test_get_issue_list(self):
        issue_list = self.project.get_issue_list()
        assert issue_list
        assert len(issue_list) >= 1

    def test_get_issue_list_author(self):
        issue_list = self.project.get_issue_list(
            status=IssueStatus.all, author="mfocko"
        )
        assert issue_list
        assert len(issue_list) >= 5

    def test_get_issue_list_nonexisting_author(self):
        issue_list = self.project.get_issue_list(
            status=IssueStatus.all, author="xyzidontexist"
        )
        assert len(issue_list) == 0

    def test_get_issue_list_assignee(self):
        issue_list = self.project.get_issue_list(
            status=IssueStatus.all, assignee="mfocko"
        )
        assert issue_list
        assert len(issue_list) >= 3

    def test_issue_info(self):
        issue_info = self.project.get_issue(1)
        assert issue_info
        assert issue_info.title.startswith("My first issue")
        assert issue_info.description.startswith("This is testing issue")

    def test_create_issue(self):
        """
        see class comment in case of fail
        """
        labels = ["label1", "label2"]
        issue_title = f"New Issue {self.random_str}"
        issue_desc = f"Description for issue {self.random_str}"
        issue = self.project.create_issue(
            title=issue_title, body=issue_desc, labels=labels
        )

        assert issue.title == issue_title
        assert issue.description == issue_desc
        for issue_label, label in zip(issue.labels, labels):
            assert issue_label == label

        issue2 = self.project.create_issue(title=issue_title, body=issue_desc)
        assert issue2.title == issue_title
        assert issue2.description == issue_desc

    def test_create_issue_with_assignee(self):
        issue_title = "This is a example issue on gitlab"
        issue_desc = "Description for issue"
        assign = ["mfocko"]
        project = self.service.get_project(repo="ogr-tests", namespace="packit-service")
        issue = project.create_issue(
            title=issue_title, body=issue_desc, assignees=assign
        )

        assert issue.title == issue_title
        assert issue.assignees[0]["username"] == assign[0]
        assert issue.description == issue_desc

    def test_create_private_issue(self):
        """
        see class comment in case of fail
        """
        issue_title = f"New Confidential Issue {self.random_str}"
        issue_desc = f"Description for issue {self.random_str}"
        issue = self.project.create_issue(
            title=issue_title, body=issue_desc, private=True
        )
        assert issue.title == issue_title
        assert issue.description == issue_desc
        assert issue.private

    def test_close_issue(self):
        """
        see class comment in case of fail
        """
        issue = self.project.create_issue(
            title=f"Close issue {self.random_str}",
            body=f"Description for issue for closing {self.random_str}",
        )
        issue_for_closing = self.project.get_issue(issue_id=issue.id)
        assert issue_for_closing.status == IssueStatus.open

        issue.close()
        assert issue.status == IssueStatus.closed

    def test_get_issue_comments(self):
        comments = self.project.get_issue(2).get_comments()
        assert len(comments) == 5
        assert comments[0].body.startswith("Comment")
        assert comments[0].author == "lbarcziova"

    def test_get_issue_comments_reversed(self):
        comments = self.project.get_issue(2).get_comments(reverse=True)
        assert len(comments) == 5
        assert comments[0].body.startswith("regex")

    def test_get_issue_comments_regex(self):
        comments = self.project.get_issue(2).get_comments(filter_regex="regex")
        assert len(comments) == 2
        assert comments[0].body.startswith("let's")

    def test_get_issue_comments_regex_reversed(self):
        comments = self.project.get_issue(2).get_comments(
            filter_regex="regex", reverse=True
        )
        assert len(comments) == 2
        assert comments[0].body.startswith("regex")

    def test_issue_labels(self):
        """
        Remove labels before regenerating:
        https://gitlab.com/packit-service/ogr-tests/issues/1
        """
        issue = self.project.get_issue(1)

        labels = issue.labels
        assert not labels

        issue.add_label("test_lb1", "test_lb2")
        labels = self.project.get_issue(1).labels
        assert len(labels) == 2
        assert labels[0] == "test_lb1"
        assert labels[1] == "test_lb2"

    def test_issue_assignees(self):
        """
        Remove the assignees from this issue before regenerating the response files:
        https://github.com/packit-service/ogr-tests/issues/1
        """
        project = self.service.get_project(repo="ogr-tests", namespace="kpostlet")
        issue = project.get_issue(1)
        assignees = issue.assignees

        assert not assignees
        issue.add_assignee("kpostlet")
        assignees = project.get_issue(1).assignees
        assert len(assignees) == 1
        assert assignees[0]["username"] == "kpostlet"

    def test_issue_list_labels(self):
        issue_list = self.project.get_issue_list(
            status=IssueStatus.all, labels=["testing-label-for-test-issue-list-labels"]
        )
        assert issue_list
        assert len(issue_list) == 33

    def test_get_issue_comments_author_regex(self):
        comments = self.project.get_issue(2).get_comments(
            filter_regex="2$", author="lbarcziova"
        )
        assert len(comments) == 1
        assert comments[0].body.startswith("Comment")

    def test_get_issue_comments_author(self):
        comments = self.project.get_issue(2).get_comments(author="mfocko")
        assert len(comments) == 2
        assert comments[0].body.startswith("let's")
        assert comments[1].body.startswith("regex")

    def test_issue_updates(self):
        issue = self.project.get_issue(issue_id=1)
        old_comments = issue.get_comments()
        issue.comment("test comment")
        new_comments = issue.get_comments()
        assert len(new_comments) > len(old_comments)

    def test_issue_comments_updates(self):
        comments = self.project.get_issue(3).get_comments(filter_regex="to be updated")
        assert len(comments) == 1
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "see if updating works"
        assert comments[0].body == "see if updating works"
        assert comments[0].edited > before_edited

        comments[0].body = before_comment
        assert comments[0].body == before_comment

    def test_setters(self):
        issue = self.project.get_issue(issue_id=1)

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

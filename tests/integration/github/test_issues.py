import pytest
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base import GithubTests
from ogr.abstract import IssueStatus
from ogr.exceptions import GithubAPIException, OperationNotSupported


@record_requests_for_all_methods()
class Issues(GithubTests):
    title = "This is a title"
    description = "This is a description"

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
        labels = ["label1", "label2"]
        issue = self.hello_world_project.create_issue(
            title=self.title, body=self.description, labels=labels
        )
        assert issue.title == self.title
        assert issue.description == self.description
        for issue_label, label in zip(issue.labels, labels):
            assert issue_label.name == label

    def test_create_private_issue(self):
        with self.assertRaises(OperationNotSupported):
            self.hello_world_project.create_issue(
                title=self.title, body=self.description, private=True
            )

    def test_create_issue_with_assignee(self):
        labels = ["label1", "label2"]
        assignee = ["lachmanfrantisek"]
        issue = self.hello_world_project.create_issue(
            title=self.title, body=self.description, labels=labels, assignees=assignee
        )
        assert issue.title == self.title
        assert issue.description == self.description
        assert issue.assignees[0].login == assignee[0]

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
        issue_info = self.ogr_project.get_issue(4)
        assert issue_info
        assert issue_info.title.startswith("Better name")
        assert issue_info.status == IssueStatus.closed

    def test_issue_labels(self):
        """
        Remove the labels from this issue before regenerating the response files:
        https://github.com/packit/ogr/issues/4
        """
        issue = self.ogr_project.get_issue(4)
        labels = issue.labels

        assert not labels
        issue.add_label("test_lb1", "test_lb2")
        labels = self.ogr_project.get_issue(4).labels
        assert len(labels) == 2
        assert labels[0].name == "test_lb1"
        assert labels[1].name == "test_lb2"

    def test_issue_assignees(self):
        """
        Remove the assignees from this issue before regenerating the response files:
        https://github.com/packit/ogr/issues/4
        """
        project = self.service.get_project(repo="ogr", namespace="KPostOffice")
        issue = project.get_issue(4)
        print(self.service.user.get_username())
        assignees = issue.assignees

        assert not assignees
        issue.add_assignee("KPostOffice")
        assignees = project.get_issue(4).assignees
        assert len(assignees) == 1
        assert assignees[0].login == "KPostOffice"

    def test_list_contains_only_issues(self):
        issue_list_all = self.ogr_project.get_issue_list(status=IssueStatus.all)
        issue_ids = [issue.id for issue in issue_list_all]

        pr_ids = [219, 207, 201, 217, 208, 210]
        for id in pr_ids:
            assert id not in issue_ids

    def test_functions_fail_for_pr(self):
        with pytest.raises(GithubAPIException):
            self.ogr_project.get_issue(1)
        with pytest.raises(GithubAPIException):
            self.ogr_project.get_issue(1).comment(body="should fail")
        with pytest.raises(GithubAPIException):
            self.ogr_project.get_issue(1).close()
        with pytest.raises(GithubAPIException):
            self.ogr_project.get_issue(1).labels
        with pytest.raises(GithubAPIException):
            self.ogr_project.get_issue(1).add_label("should fail")

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

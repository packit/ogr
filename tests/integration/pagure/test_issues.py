from requre.online_replacing import record_requests_for_all_methods

from tests.integration.pagure.base import PagureTests
from ogr.abstract import IssueStatus


@record_requests_for_all_methods()
class Issues(PagureTests):
    def setUp(self):
        super().setUp()
        self._long_issues_project = None

    @property
    def long_issues_project(self):
        if not self._long_issues_project:
            self._long_issues_project = self.service.get_project(
                repo="pagure", namespace=None
            )

        return self._long_issues_project

    def test_issue_list(self):
        issue_list = self.ogr_project.get_issue_list()
        assert isinstance(issue_list, list)

        issue_list = self.ogr_project.get_issue_list(status=IssueStatus.all)
        assert issue_list
        assert len(issue_list) >= 2

    def test_issue_list_paginated(self):
        issue_list = self.long_issues_project.get_issue_list()
        assert issue_list
        assert len(issue_list) >= 400

    def test_issue_list_author(self):
        issue_list = self.ogr_project.get_issue_list(
            status=IssueStatus.all, author="mfocko"
        )
        assert issue_list
        assert len(issue_list) >= 3

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
        assert len(issue_list) == 1

    def test_issue_list_labels(self):
        issue_list = self.ogr_project.get_issue_list(
            status=IssueStatus.all, labels=["test_label"]
        )
        assert issue_list
        assert len(issue_list) == 1

    def test_create_issue(self):
        title = "This is an issue"
        description = "Example of Issue description"
        labels = ["label1", "label2"]
        project = self.service.get_project(repo="hello-112111", namespace="testing")
        issue = project.create_issue(
            title=title, body=description, private=True, labels=labels
        )
        assert issue.title == title
        assert issue.description == description
        assert issue.private
        for issue_label, label in zip(issue.labels, labels):
            assert issue_label == label

    def test_create_issue_with_assignees(self):
        random_str = "something"
        project = self.service.get_project(repo="hello-112111", namespace="testing")
        assignee = ["mfocko"]
        issue = project.create_issue(
            title=random_str, body=random_str, assignees=assignee
        )
        assert issue.title == random_str
        assert issue.description == random_str
        assert issue.assignee == assignee[0]

    def test_issue_assignees(self):
        """
        Remove the assignees from this issue before regenerating the response files:
        https://pagure.io/testing/hello-112111/issue/4
        """

        project = self.service.get_project(
            repo="hello-112111", namespace="testing", is_fork=True
        )
        issue = project.get_issue(4)

        assert not project.get_issue(4).assignee
        issue.add_assignee("kpostlet")
        assignee = project.get_issue(4).assignee
        assert assignee == "kpostlet"

    def test_issue_without_label(self):
        title = "This is an issue"
        description = "Example of Issue description"
        project = self.service.get_project(repo="hello-112111", namespace="testing")
        issue = project.create_issue(title=title, body=description)
        assert issue.title == title
        assert issue.description == description

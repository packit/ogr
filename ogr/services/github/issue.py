# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import List, Optional, Dict, Union

import github
from github import UnknownObjectException
from github.Issue import Issue as _GithubIssue

from ogr.abstract import Issue, IssueComment, IssueStatus
from ogr.exceptions import GithubAPIException, OperationNotSupported
from ogr.services import github as ogr_github
from ogr.services.base import BaseIssue
from ogr.services.github.comments import GithubIssueComment


class GithubIssue(BaseIssue):
    raw_issue: _GithubIssue

    def __init__(
        self, raw_issue: _GithubIssue, project: "ogr_github.GithubProject"
    ) -> None:
        if raw_issue.pull_request:
            raise GithubAPIException(
                f"Requested issue #{raw_issue.number} is a pull request"
            )

        super().__init__(raw_issue=raw_issue, project=project)

    @property
    def title(self) -> str:
        return self._raw_issue.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_issue.edit(title=new_title)

    @property
    def id(self) -> int:
        return self._raw_issue.number

    @property
    def status(self) -> IssueStatus:
        return IssueStatus[self._raw_issue.state]

    @property
    def url(self) -> str:
        return self._raw_issue.html_url

    @property
    def assignees(self) -> list:
        return self._raw_issue.assignees

    @property
    def description(self) -> str:
        return self._raw_issue.body

    @description.setter
    def description(self, new_description: str) -> None:
        self._raw_issue.edit(body=new_description)

    @property
    def author(self) -> str:
        return self._raw_issue.user.login

    @property
    def created(self) -> datetime.datetime:
        return self._raw_issue.created_at

    @property
    def labels(self) -> List:
        return list(self._raw_issue.get_labels())

    def __str__(self) -> str:
        return "Github" + super().__str__()

    @staticmethod
    def create(
        project: "ogr_github.GithubProject",
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[list] = None,
    ) -> "Issue":
        if private:
            raise OperationNotSupported("Private issues are not supported by Github")

        github_issue = project.github_repo.create_issue(
            title=title, body=body, labels=labels or [], assignees=assignees or []
        )
        return GithubIssue(github_issue, project)

    @staticmethod
    def get(project: "ogr_github.GithubProject", issue_id: int) -> "Issue":
        try:
            issue = project.github_repo.get_issue(number=issue_id)
        except github.UnknownObjectException as ex:
            raise GithubAPIException(f"No issue with id {issue_id} found") from ex
        return GithubIssue(issue, project)

    @staticmethod
    def get_list(
        project: "ogr_github.GithubProject",
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List["Issue"]:
        parameters: Dict[str, Union[str, List[str]]] = {
            "state": status.name,
            "sort": "updated",
            "direction": "desc",
        }
        if author:
            parameters["creator"] = author
        if assignee:
            parameters["assignee"] = assignee
        if labels:
            parameters["labels"] = [
                project.github_repo.get_label(label) for label in labels
            ]

        issues = project.github_repo.get_issues(**parameters)
        try:
            return [
                GithubIssue(issue, project)
                for issue in issues
                if not issue.pull_request
            ]
        except UnknownObjectException:
            return []

    def _get_all_comments(self) -> List[IssueComment]:
        return [
            GithubIssueComment(parent=self, raw_comment=raw_comment)
            for raw_comment in self._raw_issue.get_comments()
        ]

    def comment(self, body: str) -> IssueComment:
        comment = self._raw_issue.create_comment(body)
        return GithubIssueComment(parent=self, raw_comment=comment)

    def close(self) -> "Issue":
        self._raw_issue.edit(state="closed")
        return self

    def add_label(self, *labels: str) -> None:
        for label in labels:
            self._raw_issue.add_to_labels(label)

    def add_assignee(self, *assignees: str) -> None:
        try:
            self._raw_issue.edit(assignees=list(assignees))
        except github.GithubException as ex:
            raise GithubAPIException("Failed to assign issue, unknown user") from ex

    def get_comment(self, comment_id: int) -> IssueComment:
        return GithubIssueComment(self._raw_issue.get_comment(comment_id))

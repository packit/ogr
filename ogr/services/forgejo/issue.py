# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
from datetime import datetime
from typing import Optional, Union

import pyforgejo.types.issue as _issue

from ogr.abstract import Issue, IssueComment, IssueStatus
from ogr.exceptions import IssueTrackerDisabled, OperationNotSupported
from ogr.services import forgejo
from ogr.services.base import BaseIssue
from ogr.services.forgejo.comments import ForgejoIssueComment


class ForgejoIssue(BaseIssue):
    project: "forgejo.ForgejoProject"

    def __init__(self, raw_issue: _issue, project: "forgejo.ForgejoProject"):
        super().__init__(raw_issue, project)
        self._raw_issue = raw_issue

    @property
    def _index(self):
        return self._raw_issue.number

    @property
    def title(self) -> str:
        return self._raw_issue.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._issue_api_call(
            self.project.service.api.issue.edit_issue,
            title=new_title,
        )

    @property
    def id(self) -> int:
        return self._raw_issue.id

    @property
    def url(self) -> str:
        return self._raw_issue.url

    @property
    def description(self) -> str:
        return self._raw_issue.body

    @property
    def author(self) -> str:
        return self._raw_issue.user.login

    @property
    def created(self) -> datetime:
        return self._raw_issue.created_at

    @property
    def status(self) -> IssueStatus:
        return IssueStatus[self._raw_issue.state]

    @property
    def assignees(self) -> list:
        try:
            return self._raw_issue.assignees
        except AttributeError:
            return None

    @staticmethod
    def create(
        project: "forgejo.ForgejoProject",
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> "Issue":

        if private:
            raise NotImplementedError()
        if not project.has_issues:
            raise IssueTrackerDisabled()

        issue = project.service.api.issue.create_issue(
            owner=project.namespace,
            repo=project.repo,
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
        )
        return ForgejoIssue(issue, project)

    @staticmethod
    def get(project: "forgejo.ForgejoProject", issue_id: int) -> _issue:
        if not project.has_issues:
            raise IssueTrackerDisabled

        try:
            issue = project.service.api.issue.get_issue(
                owner=project.namespace, repo=project.repo, index=issue_id,
            )
        except Exception as ex:
            raise OperationNotSupported(f"Issue {issue_id} not found") from ex
        return ForgejoIssue(issue, project)

    @staticmethod
    def get_list(
        project: "forgejo.ForgejoProject",
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list["Issue"]:
        if not project.has_issues:
            raise IssueTrackerDisabled

        parameters: dict[str, Union[str, list[str], bool]] = {
            "state": status if status != IssueStatus.open else "open",
            "type": "issues",
        }
        if author:
            parameters["created_by"] = author
        if assignee:
            parameters["assigned_by"] = assignee
        if labels:
            parameters["labels"] = labels

        issues = project.service.api.issue.list_issues(
            owner=project.namespace, repo=project.repo, **parameters,
        )
        return [ForgejoIssue(issue, project) for issue in issues]

    def close(self) -> "Issue":
        self._issue_api_call(
            self.project.service.api.issue.edit_issue,
            state="closed",
        )
        return self

    def add_label(self, *labels: str) -> None:
        self._issue_api_call(
            self.project.service.api.issue.add_label,
            labels=list(labels),
        )

    def comment(self, body: str) -> IssueComment:
        comment = self._issue_api_call(
            self.project.service.api.issue.create_comment,
            body=body,
        )
        return ForgejoIssueComment(self, comment)

    def _get_all_comments(self) -> list[IssueComment]:
        comments = self._issue_api_call(self.project.service.api.issue.get_comments)
        return [
            ForgejoIssueComment(raw_comment=comment, parent=self)
            for comment in comments
        ]

    def _issue_api_call(self, method, **kwargs):
        params = {
            "owner": self.project.namespace,
            "repo": self.project.repo,
            "index": self._index,
        }
        params.update(kwargs)
        return method(**params)

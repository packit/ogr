# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
import re
from datetime import datetime
from typing import Any, Optional, Type, Union

import pyforgejo.types.issue as _issue
from pyforgejo import NotFoundError

from ogr.abstract import Issue, IssueComment, IssueLabel, IssueStatus
from ogr.exceptions import IssueTrackerDisabled
from ogr.services import forgejo
from ogr.services.base import BaseIssue
from ogr.services.forgejo.comments import ForgejoIssueComment
from ogr.services.forgejo.label import ForgejoIssueLabel


class ForgejoIssue(BaseIssue):
    project: "forgejo.ForgejoProject"

    def __init__(self, raw_issue: _issue, project: "forgejo.ForgejoProject"):
        super().__init__(raw_issue, project)
        self._raw_issue = raw_issue

    @property
    def _index(self):
        return self._raw_issue.number

    def __update_info(self) -> None:
        """Refresh the local issue object with the latest data from the server."""
        self._raw_issue = self.project.service.api.issue.get_issue(
            owner=self.project.namespace,
            repo=self.project.repo,
            index=self._index,
        )

    @property
    def title(self) -> str:
        return self._raw_issue.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._api_call(
            self.project.service.api.issue.edit_issue,
            title=new_title,
        )
        self.__update_info()

    @property
    def id(self) -> int:
        return self._raw_issue.number

    @property
    def url(self) -> str:
        return self._raw_issue.url

    @property
    def description(self) -> str:
        return self._raw_issue.body

    @description.setter
    def description(self, text: str):
        self._api_call(self.project.service.api.issue.edit_issue, body=text)
        self.__update_info()

    @property
    def author(self) -> str:
        return self._raw_issue.user.login

    @property
    def created(self) -> datetime:
        return self._raw_issue.created_at

    @property
    def status(self) -> Type[IssueStatus[Any]]:
        return IssueStatus[self._raw_issue.state]

    @property
    def assignees(self) -> list:
        return getattr(self._raw_issue, "assignees", []) or []

    @property
    def labels(self) -> list["IssueLabel"]:
        labels = self._api_call(self.project.service.api.issue.get_labels)
        return [ForgejoIssueLabel(label.name, self) for label in labels]

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
            raise IssueTrackerDisabled()

        try:
            issue = project.service.api.issue.get_issue(
                owner=project.namespace,
                repo=project.repo,
                index=issue_id,
            )
        except Exception as ex:
            raise NotFoundError(f"Issue {issue_id} not found") from ex
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
            raise IssueTrackerDisabled()

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
        try:
            issues = project.service.api.issue.list_issues(
                owner=project.namespace,
                repo=project.repo,
                **parameters,
            )
        except NotFoundError as ex:
            if "user does not exist" in str(ex):
                return []
            raise NotFoundError(f"Failed to list issues {ex}") from ex
        return [ForgejoIssue(issue, project) for issue in issues]

    def close(self) -> "Issue":
        self._api_call(
            self.project.service.api.issue.edit_issue,
            state="closed",
        )
        self._raw_issue = self.project.service.api.issue.get_issue(
            owner=self.project.namespace,
            repo=self.project.repo,
            index=self._index,
        )
        return self

    def comment(self, body: str) -> IssueComment:
        comment = self._api_call(
            self.project.service.api.issue.create_comment,
            body=body,
        )
        return ForgejoIssueComment(parent=self, raw_comment=comment)

    def get_comment(self, comment_id: int) -> IssueComment:
        comment = self.project.service.api.issue.get_comment(
            owner=self.project.namespace,
            repo=self.project.repo,
            id=comment_id,
        )
        return ForgejoIssueComment(raw_comment=comment, parent=self)

    def get_comments(
        self,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> list[IssueComment]:
        comments = self._get_all_comments()
        if filter_regex:
            comments = [
                comment
                for comment in comments
                if comment.body and re.search(filter_regex, comment.body)
            ]
        if author:
            comments = [
                comment
                for comment in comments
                if comment.author and comment.author == author
            ]
        if reverse:
            comments = comments[::-1]

        return comments

    def _get_all_comments(self) -> list[IssueComment]:
        comments = self._api_call(self.project.service.api.issue.get_comments)
        return [
            ForgejoIssueComment(raw_comment=comment, parent=self)
            for comment in comments
        ]

    def add_assignee(self, *assignees: str) -> None:
        current_assignees = [
            assignee.login if hasattr(assignee, "login") else assignee
            for assignee in self.assignees
        ]
        updated_assignees = list(set(current_assignees + list(assignees)))
        self._api_call(
            self.project.service.api.issue.edit_issue,
            assignees=updated_assignees,
        )
        self.__update_info()

    def add_label(self, *labels: str) -> None:
        self._api_call(self.project.service.api.issue.add_label, labels=labels)
        self.__update_info()

    def _api_call(self, method, **kwargs):
        params = {
            "owner": self.project.namespace,
            "repo": self.project.repo,
            "index": self._index,
        }
        params.update(kwargs)
        return method(**params)

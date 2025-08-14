# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
from datetime import datetime
from functools import partial
from typing import Optional, Union

import pyforgejo.types.issue as _issue
from pyforgejo import NotFoundError

from ogr.abstract import Issue, IssueStatus
from ogr.exceptions import IssueTrackerDisabled, OperationNotSupported
from ogr.services import forgejo
from ogr.services.base import BaseIssue
from ogr.services.forgejo.comments import ForgejoIssueComment
from ogr.services.forgejo.utils import paginate


class ForgejoIssue(BaseIssue):
    project: "forgejo.ForgejoProject"

    def __init__(self, raw_issue: _issue, project: "forgejo.ForgejoProject"):
        super().__init__(raw_issue, project)
        self._raw_issue = raw_issue

    @property
    def _index(self):
        return self._raw_issue.number

    @property
    def api(self):
        """Returns the issue API client from pyforgejo."""
        return self.project.service.api.issue

    def partial_api(self, method, /, *args, **kwargs):
        """Returns a partial API call for ForgejoIssue.


        Injects owner, repo, and index parameters for the calls to issue API endpoints.

        Args:
            method: Specific method on the Pyforgejo API that is to be wrapped.
            *args: Positional arguments that get injected into every call.
            **kwargs: Keyword-arguments that get injected into every call.

        Returns:
            Callable with pre-injected parameters.
        """
        params = {"owner": self.project.namespace, "repo": self.project.repo}

        # Include the issue index only for methods that need it
        if "get_issue" in str(method) or "edit_issue" in str(method):
            params["index"] = self._index

        return partial(method, *args, **kwargs, **params)

    @property
    def title(self) -> str:
        return self._raw_issue.title

    @title.setter
    def title(self, new_title: str) -> None:
        self.partial_api(self.api.edit_issue)(title=new_title)

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
        self.partial_api(self.api.edit_issue)(body=text)

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
        return getattr(self._raw_issue, "assignees", []) or []

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
    def get(project: "forgejo.ForgejoProject", issue_id: int) -> "Issue":
        if not project.has_issues:
            raise IssueTrackerDisabled()

        try:
            issue = project.service.api.issue.get_issue(
                owner=project.namespace,
                repo=project.repo,
                index=issue_id,
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
            raise IssueTrackerDisabled()

        parameters: dict[str, Union[str, list[str], bool]] = {
            "state": status.name,
            "type": "issues",
        }
        if author:
            parameters["created_by"] = author
        if assignee:
            parameters["assigned_by"] = assignee

        if labels:
            parameters["labels"] = labels
        try:
            return [
                ForgejoIssue(issue, project)
                for issue in paginate(
                    project.service.api.issue.list_issues,
                    owner=project.namespace,
                    repo=project.repo,
                    **parameters,
                )
            ]
        except NotFoundError as ex:
            if "user does not exist" in str(ex):
                return []
            raise OperationNotSupported(f"Failed to list issues {ex}") from ex

    def close(self) -> "Issue":
        self.partial_api(self.api.edit_issue)(state="closed")

        return self

    def get_comments(self):
        return [
            ForgejoIssueComment(comment, parent=self)
            for comment in self.api.get_comments(
                owner=self.project.namespace,
                repo=self.project.repo,
                index=self._index,
            )
        ] or []

    def get_comment(self, comment_id: int):
        return ForgejoIssueComment(
            self.api.get_comment(
                owner=self.project.namespace,
                repo=self.project.repo,
                id=comment_id,
            ),
            parent=self,
        )

    def add_assignee(self, *assignees: str) -> None:
        current_assignees = [
            assignee.login if hasattr(assignee, "login") else assignee
            for assignee in self.assignees
        ]
        updated_assignees = list(set(current_assignees + list(assignees)))
        self.partial_api(self.api.edit_issue)(assignees=updated_assignees)

    def add_label(self, *labels: str) -> None:
        self.partial_api(self.api.add_label)(labels=labels, index=self._index)

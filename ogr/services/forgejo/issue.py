# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
import itertools
from collections.abc import Iterable
from datetime import datetime
from functools import partial
from typing import Optional, Union

from pyforgejo import NotFoundError
from pyforgejo.core.api_error import ApiError
from pyforgejo.types import User as PyforgejoUser
from pyforgejo.types.issue import Issue as _issue

from ogr.abstract import Issue, IssueComment, IssueLabel, IssueStatus
from ogr.exceptions import (
    ForgejoAPIException,
    IssueTrackerDisabled,
    OperationNotSupported,
)
from ogr.services import forgejo
from ogr.services.base import BaseIssue
from ogr.services.forgejo.comments import ForgejoIssueComment
from ogr.services.forgejo.label import ForgejoIssueLabel
from ogr.services.forgejo.utils import paginate


class ForgejoIssue(BaseIssue):
    project: "forgejo.ForgejoProject"

    def __init__(self, raw_issue: _issue, project: "forgejo.ForgejoProject"):
        if raw_issue.pull_request:
            raise ForgejoAPIException(
                f"Requested issue #{raw_issue.number} is a pull request",
            )

        super().__init__(raw_issue, project)

    @property
    def api(self):
        """Returns the issue API client from pyforgejo."""
        return self.project.service.api.issue

    def partial_api(self, method, /, *args, **kwargs):
        """Returns a partial API call for ForgejoIssue.


        Injects owner and repo parameters for the calls to issue API endpoints.

        Args:
            method: Specific method on the Pyforgejo API that is to be wrapped.
            *args: Positional arguments that get injected into every call.
            **kwargs: Keyword-arguments that get injected into every call.

        Returns:
            Callable with pre-injected parameters.
        """
        params = {"owner": self.project.namespace, "repo": self.project.repo}
        return partial(method, *args, **kwargs, **params)

    def __update_info(self) -> None:
        """Refresh the local issue object with the latest data from the server."""
        self._raw_issue = self.partial_api(self.api.get_issue)(index=self.id)

    @property
    def title(self) -> str:
        return self._raw_issue.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_issue = self.partial_api(self.api.edit_issue)(
            title=new_title,
            index=self.id,
        )

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
    def description(self, new_description: str):
        self._raw_issue = self.partial_api(self.api.edit_issue)(
            body=new_description,
            index=self.id,
        )

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
    def assignees(self) -> list[PyforgejoUser]:
        return self._raw_issue.assignees or []

    @property
    def labels(self) -> list[IssueLabel]:
        return [
            ForgejoIssueLabel(raw_label, self) for raw_label in self._raw_issue.labels
        ]

    def __str__(self) -> str:
        return "Forgejo" + super().__str__()

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
            raise OperationNotSupported("Private issues are not supported by Forgejo")
        if not project.has_issues:
            raise IssueTrackerDisabled()

        # The API requires ids of labels in the create_issue method
        # which would lead to having to retrieve existing labels and
        # needing to find the ids of those we need to add to the issue;
        # A separate API call would also need to be made to create each
        # label that does not yet exist, potentially leading to many
        # API calls and unclear code, so labels are instead added seprately
        # below after creating a new issue without labels
        issue = project.service.api.issue.create_issue(
            owner=project.namespace,
            repo=project.repo,
            title=title,
            body=body,
            labels=[],
            assignees=assignees,
        )

        forgejo_issue = ForgejoIssue(issue, project)

        if labels:
            forgejo_issue.add_label(*labels)

        return forgejo_issue

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

        except NotFoundError as ex:
            raise ForgejoAPIException(f"Issue {issue_id} not found") from ex
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
            raise ForgejoAPIException("Failed to list issues") from ex

    def comment(self, body: str) -> IssueComment:
        comment = self.partial_api(self.api.create_comment)(
            body=body,
            index=self.id,
        )
        return ForgejoIssueComment(parent=self, raw_comment=comment)

    def close(self) -> "Issue":
        self._raw_issue = self.partial_api(self.api.edit_issue)(
            state="closed",
            index=self.id,
        )

        return self

    def _get_all_comments(self, reverse: bool = False) -> Iterable[IssueComment]:
        comments = self.partial_api(self.api.get_comments)(
            index=self.id,
        )

        if reverse:
            comments = list(reversed(comments))

        return (
            ForgejoIssueComment(parent=self, raw_comment=raw_comment)
            for raw_comment in comments
        )

    def get_comment(self, comment_id: int) -> ForgejoIssueComment:
        return ForgejoIssueComment(
            self.partial_api(self.api.get_comment)(id=comment_id),
            parent=self,
        )

    def add_assignee(self, *assignees: str) -> None:
        current_assignees = [assignee.login for assignee in self.assignees]
        updated_assignees = set(itertools.chain(current_assignees, assignees))

        try:
            self._raw_issue = self.partial_api(self.api.edit_issue)(
                assignees=updated_assignees,
                index=self.id,
            )
        except ApiError as ex:
            raise ForgejoAPIException(
                "Failed to assign issue, unknown user",
            ) from ex

    def add_label(self, *labels: str) -> None:
        self.partial_api(self.api.add_label)(labels=labels, index=self.id)
        self.__update_info()

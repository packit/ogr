# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from collections.abc import Iterable
from typing import Any, Optional, Union

from ogr import abstract as _abstract
from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.status import IssueStatus


class Issue(OgrAbstractClass):
    """
    Attributes:
        project (GitProject): Project of the issue.
    """

    def __init__(self, raw_issue: Any, project: "_abstract.GitProject") -> None:
        self._raw_issue = raw_issue
        self.project = project

    @property
    def title(self) -> str:
        """Title of the issue."""
        raise NotImplementedError()

    @property
    def private(self) -> bool:
        """`True` if issue is confidential, `False` otherwise."""
        raise NotImplementedError()

    @property
    def id(self) -> int:
        """ID of the issue."""
        raise NotImplementedError()

    @property
    def status(self) -> IssueStatus:
        """Status of the issue."""
        raise NotImplementedError()

    @property
    def url(self) -> str:
        """Web URL of the issue."""
        raise NotImplementedError()

    @property
    def description(self) -> str:
        """Description of the issue."""
        raise NotImplementedError()

    @property
    def author(self) -> str:
        """Username of the author of the issue."""
        raise NotImplementedError()

    @property
    def created(self) -> datetime.datetime:
        """Datetime of the creation of the issue."""
        raise NotImplementedError()

    @property
    def labels(
        self,
    ) -> Union[list["_abstract.IssueLabel"], Iterable["_abstract.IssueLabel"]]:
        """Labels of the issue."""
        raise NotImplementedError()

    def __str__(self) -> str:
        description = (
            f"{self.description[:10]}..." if self.description is not None else "None"
        )
        return (
            f"Issue("
            f"title='{self.title}', "
            f"id={self.id}, "
            f"status='{self.status.name}', "
            f"url='{self.url}', "
            f"description='{description}', "
            f"author='{self.author}', "
            f"created='{self.created}')"
        )

    @staticmethod
    def create(
        project: Any,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> "Issue":
        """
        Open new issue.

        Args:
            project (GitProject): Project where the issue is to be opened.
            title: Title of the issue.
            body: Description of the issue.
            private: Is the new issue supposed to be confidential?

                **Supported only by GitLab and Pagure.**

                Defaults to unset.
            labels: List of labels that are to be added to
                the issue.

                Defaults to no labels.
            assignees: List of usernames of the assignees.

                Defaults to no assignees.

        Returns:
            Object that represents newly created issue.
        """
        raise NotImplementedError()

    @staticmethod
    def get(project: Any, id: int) -> "Issue":
        """
        Get issue.

        Args:
            project (GitProject): Project where the issue is to be opened.
            issue_id: ID of the issue.

        Returns:
            Object that represents requested issue.
        """
        raise NotImplementedError()

    @staticmethod
    def get_list(
        project: Any,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> Union[list["Issue"], Iterable["Issue"]]:
        """
        List of issues.

        Args:
            project (GitProject): Project where the issue is to be opened.
            status: Status of the issues that are to be
                included in the list.

                Defaults to `IssueStatus.open`.
            author: Username of the author of the issues.

                Defaults to no filtering by author.
            assignee: Username of the assignee on the issues.

                Defaults to no filtering by assignees.
            labels: Filter issues that have set specific labels.

                Defaults to no filtering by labels.

        Returns:
            List of objects that represent requested issues.
        """
        raise NotImplementedError()

    def _get_all_comments(
        self,
        reverse: bool = False,
    ) -> Union[list["_abstract.IssueComment"], Iterable["_abstract.IssueComment"]]:
        """
        Get list of all issue comments.

        Args:
            reverse: Defines whether the comments should be listed in a reversed
                order.

                Defaults to `False`.

        Returns:
            List of all comments on the issue.
        """
        raise NotImplementedError()

    def get_comments(
        self,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> Union[list["_abstract.IssueComment"], Iterable["_abstract.IssueComment"]]:
        """
        Get list of issue comments.

        Args:
            filter_regex: Filter the comments' content with `re.search`.

                Defaults to `None`, which means no filtering.
            reverse: Whether the comments are to be returned in
                reversed order.

                Defaults to `False`.
            author: Filter the comments by author.

                Defaults to `None`, which means no filtering.

        Returns:
            List of issue comments.
        """
        raise NotImplementedError()

    def can_close(self, username: str) -> bool:
        """
        Check if user have permissions to modify an issue.

        Args:
            username: Login of the user.

        Returns:
            `True` if user can close the issue, `False` otherwise.
        """
        raise NotImplementedError()

    def comment(self, body: str) -> "_abstract.IssueComment":
        """
        Add new comment to the issue.

        Args:
            body: Text contents of the comment.

        Returns:
            Object that represents posted comment.
        """
        raise NotImplementedError()

    def close(self) -> "Issue":
        """
        Close an issue.

        Returns:
            Issue itself.
        """
        raise NotImplementedError()

    def add_label(self, *labels: str) -> None:
        """
        Add labels to the issue.

        Args:
            *labels: Labels to be added.
        """
        raise NotImplementedError()

    def add_assignee(self, *assignees: str) -> None:
        """
        Assign users to an issue.

        Args:
            *assignees: List of logins of the assignees.
        """
        raise NotImplementedError()

    def get_comment(self, comment_id: int) -> "_abstract.IssueComment":
        """
        Returns an issue comment.

        Args:
            comment_id: id of a comment

        Returns:
            Object representing an issue comment.
        """
        raise NotImplementedError()

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any

from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.issue import Issue
from ogr.abstract.pull_request import PullRequest


class Label(OgrAbstractClass):
    """
    Represents labels on PRs and issues.
    """

    def __init__(self, parent: Any) -> None:
        self._parent = parent

    @property
    def name(self) -> str:
        """Name of the label."""
        raise NotImplementedError()


class IssueLabel(Label):
    @property
    def issue(self) -> "Issue":
        """Issue of issue label."""
        return self._parent

    def __str__(self) -> str:
        return "Issue" + super().__str__()


class PRLabel(Label):
    @property
    def pull_request(self) -> "PullRequest":
        """Pull request of pull request label."""
        return self._parent

    def __str__(self) -> str:
        return "PR" + super().__str__()

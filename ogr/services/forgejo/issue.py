# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

from pyforgejo.types import Issue as PyforgejoIssue

from ogr.abstract import Issue, IssueStatus
from ogr.services import forgejo
from ogr.services.base import BaseIssue


class ForgejoIssue(BaseIssue):
    def __init__(self, raw_issue: PyforgejoIssue, project: "forgejo.ForgejoProject"):
        super().__init__(raw_issue, project)

    @staticmethod
    def create(
        project: "forgejo.ForgejoProject",
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list] = None,
    ) -> "Issue":
        raise NotImplementedError("TBD")

    @staticmethod
    def get(project: "forgejo.ForgejoProject", issue_id: int) -> "Issue":
        raise NotImplementedError("TBD")

    @staticmethod
    def get_list(
        project: "forgejo.ForgejoProject",
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list["Issue"]:
        raise NotImplementedError("TBD")

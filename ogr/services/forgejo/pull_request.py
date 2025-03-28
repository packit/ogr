# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

from pyforgejo.types import PullRequest as PyforgejoPullRequest

from ogr.abstract import PRStatus, PullRequest
from ogr.services import forgejo
from ogr.services.base import BasePullRequest


class ForgejoPullRequest(BasePullRequest):
    def __init__(
        self,
        raw_pr: PyforgejoPullRequest,
        project: "forgejo.ForgejoProject",
    ):
        super().__init__(raw_pr, project)

    @staticmethod
    def create(
        project: "forgejo.ForgejoProject",
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> "PullRequest":
        raise NotImplementedError("TBD")

    @staticmethod
    def get(project: "forgejo.ForgejoProject", pr_id: int) -> "PullRequest":
        raise NotImplementedError("TBD")

    @staticmethod
    def get_list(
        project: "forgejo.ForgejoProject",
        status: PRStatus = PRStatus.open,
    ) -> list["PullRequest"]:
        raise NotImplementedError("TBD")

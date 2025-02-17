# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any

from ogr.services import forgejo
from ogr.services.base import BasePullRequest


class ForgejoPullRequest(BasePullRequest):
    def __init__(
        self,
        raw_pr: Any,
        project: "forgejo.ForgejoProject",
    ):
        super().__init__(raw_pr, project)

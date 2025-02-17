# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from ogr.services import forgejo
from ogr.services.base import BaseIssue


class ForgejoIssue(BaseIssue):
    def __init__(self, raw_issue, project: "forgejo.ForgejoProject"):
        super().__init__(raw_issue, project)

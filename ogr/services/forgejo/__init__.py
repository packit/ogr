# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from ogr.services.forgejo.comments import (
    ForgejoComment,
    ForgejoIssueComment,
    ForgejoPRComment,
)
from ogr.services.forgejo.issue import ForgejoIssue
from ogr.services.forgejo.project import ForgejoProject
from ogr.services.forgejo.pull_request import ForgejoPullRequest
from ogr.services.forgejo.release import ForgejoRelease
from ogr.services.forgejo.service import ForgejoService
from ogr.services.forgejo.user import ForgejoUser

__all__ = [
    ForgejoPullRequest.__name__,
    ForgejoComment.__name__,
    ForgejoIssueComment.__name__,
    ForgejoPRComment.__name__,
    ForgejoIssue.__name__,
    ForgejoProject.__name__,
    ForgejoRelease.__name__,
    ForgejoService.__name__,
    ForgejoUser.__name__,
]

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from typing import Union

from ogr.abstract import CommitStatus
from ogr.services import forgejo as ogr_forgejo
from ogr.services.base import BaseCommitFlag


class ForgejoCommitFlag(BaseCommitFlag):
    @staticmethod
    def set(
        project: "ogr_forgejo.ForgejoProject",
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "ForgejoCommitFlag":
        raise NotImplementedError("TBD")

    @staticmethod
    def get(
        project: "ogr_forgejo.ForgejoProject",
        commit: str,
    ) -> Iterable["ForgejoCommitFlag"]:
        raise NotImplementedError("TBD")

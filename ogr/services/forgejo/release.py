# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

from ogr.abstract import Release
from ogr.services import forgejo as ogr_forgejo


class ForgejoRelease(Release):
    @staticmethod
    def get(
        project: "ogr_forgejo.ForgejoProject",
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "Release":
        raise NotImplementedError("TBD")

    @staticmethod
    def get_latest(project: "ogr_forgejo.ForgejoProject") -> Optional["Release"]:
        raise NotImplementedError("TBD")

    @staticmethod
    def get_list(project: "ogr_forgejo.ForgejoProject") -> list["Release"]:
        raise NotImplementedError("TBD")

    @staticmethod
    def create(
        project: "ogr_forgejo.ForgejoProject",
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "Release":
        raise NotImplementedError("TBD")

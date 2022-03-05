# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import List, Optional

from ogr.abstract import GitTag, Release
from ogr.services import pagure as ogr_pagure
from ogr.exceptions import OperationNotSupported, PagureAPIException


class PagureRelease(Release):
    _raw_release: GitTag
    project: "ogr_pagure.PagureProject"

    @property
    def title(self):
        return self.git_tag.name

    @property
    def body(self):
        return ""

    @property
    def git_tag(self) -> GitTag:
        return self._raw_release

    @property
    def tag_name(self) -> str:
        return self._raw_release.name

    @property
    def url(self) -> Optional[str]:
        return ""

    @property
    def created_at(self) -> datetime.datetime:
        return None

    @property
    def tarball_url(self) -> str:
        return ""

    def __str__(self) -> str:
        return "Pagure" + super().__str__()

    @staticmethod
    def get(
        project: "ogr_pagure.PagureProject",
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "Release":
        raise OperationNotSupported()

    @staticmethod
    def get_latest(project: "ogr_pagure.PagureProject") -> Optional["Release"]:
        raise OperationNotSupported("Pagure API does not provide timestamps")

    @staticmethod
    def get_list(project: "ogr_pagure.PagureProject") -> List["Release"]:
        # git tag for Pagure is shown as Release in Pagure UI
        git_tags = project.get_tags()
        return [PagureRelease(git_tag, project) for git_tag in git_tags]

    @staticmethod
    def create(
        project: "ogr_pagure.PagureProject",
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "Release":
        payload = {
            "tagname": tag,
            "commit_hash": ref,
        }
        if message:
            payload["message"] = message

        response = project._call_project_api("git", "tags", data=payload, method="POST")
        if not response["tag_created"]:
            raise PagureAPIException("Release has not been created")

        return PagureRelease(GitTag(tag, ref), project)

    def edit_release(self, name: str, message: str) -> None:
        raise OperationNotSupported("edit_release not supported on Pagure")

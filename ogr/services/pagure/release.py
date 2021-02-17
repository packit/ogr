# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from ogr.abstract import GitTag, Release
from ogr.services import pagure as ogr_pagure
from ogr.exceptions import OperationNotSupported


class PagureRelease(Release):
    project: "ogr_pagure.PagureProject"

    def __init__(
        self,
        tag_name: str,
        url: str,
        created_at: str,
        tarball_url: str,
        git_tag: GitTag,
        project: "ogr_pagure.PagureProject",
    ) -> None:
        super().__init__(tag_name, url, created_at, tarball_url, git_tag, project)

    @property
    def title(self):
        return self.git_tag.name

    @property
    def body(self):
        return ""

    def edit_release(self, name: str, message: str) -> None:
        raise OperationNotSupported("edit_release not supported on Pagure")

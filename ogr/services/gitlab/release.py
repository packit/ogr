# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

from ogr.abstract import Release, GitTag
from ogr.services import gitlab as ogr_gitlab
from ogr.exceptions import OperationNotSupported


class GitlabRelease(Release):
    project: "ogr_gitlab.GitlabProject"

    def __init__(
        self,
        tag_name: str,
        url: Optional[str],
        created_at: str,
        tarball_url: str,
        git_tag: GitTag,
        project: "ogr_gitlab.GitlabProject",
        raw_release,
    ) -> None:
        super().__init__(tag_name, url, created_at, tarball_url, git_tag, project)
        self.raw_release = raw_release

    @property
    def title(self):
        return self.raw_release.name

    @property
    def body(self):
        return self.raw_release.description

    def edit_release(self, name: str, message: str) -> None:
        raise OperationNotSupported("edit_release not supported on GitLab")

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from github.GitRelease import GitRelease as PyGithubRelease

from ogr.abstract import Release, GitTag
from ogr.services import github as ogr_github


class GithubRelease(Release):
    project: "ogr_github.GithubProject"

    def __init__(
        self,
        tag_name: str,
        url: str,
        created_at: str,
        tarball_url: str,
        git_tag: GitTag,
        project: "ogr_github.GithubProject",
        raw_release: PyGithubRelease,
    ) -> None:
        super().__init__(tag_name, url, created_at, tarball_url, git_tag, project)
        self.raw_release = raw_release

    @property
    def title(self):
        return self.raw_release.title

    @property
    def body(self):
        return self.raw_release.body

    def edit_release(self, name: str, message: str) -> None:
        """
        Edit name and message of a release.

        Args:
            name: New name of the release.
            message: New message for the release.
        """
        self.raw_release = self.raw_release.update_release(name=name, message=message)

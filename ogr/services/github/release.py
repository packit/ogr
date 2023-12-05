# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import Optional

from github import GithubException
from github.GitRelease import GitRelease as PyGithubRelease

from ogr.abstract import GitTag, Release
from ogr.exceptions import GithubAPIException
from ogr.services import github as ogr_github


class GithubRelease(Release):
    _raw_release: PyGithubRelease
    project: "ogr_github.GithubProject"

    @staticmethod
    def _release_id_from_name(
        project: "ogr_github.GithubProject",
        name: str,
    ) -> Optional[int]:
        releases = project.github_repo.get_releases()
        for release in releases:
            if release.title == name:
                return release.id
        return None

    @staticmethod
    def _release_id_from_tag(
        project: "ogr_github.GithubProject",
        tag: str,
    ) -> Optional[int]:
        releases = project.github_repo.get_releases()
        for release in releases:
            if release.tag_name == tag:
                return release.id
        return None

    @property
    def title(self):
        return self._raw_release.title

    @property
    def body(self):
        return self._raw_release.body

    @property
    def git_tag(self) -> GitTag:
        return self.project.get_tag_from_tag_name(self.tag_name)

    @property
    def tag_name(self) -> str:
        return self._raw_release.tag_name

    @property
    def url(self) -> Optional[str]:
        return self._raw_release.html_url

    @property
    def created_at(self) -> datetime.datetime:
        return self._raw_release.created_at

    @property
    def tarball_url(self) -> str:
        return self._raw_release.tarball_url

    def __str__(self) -> str:
        return "Github" + super().__str__()

    @staticmethod
    def get(
        project: "ogr_github.GithubProject",
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "Release":
        if tag_name:
            identifier = GithubRelease._release_id_from_tag(project, tag_name)
        elif name:
            identifier = GithubRelease._release_id_from_name(project, name)
        if identifier is None:
            raise GithubAPIException("Release was not found.")
        release = project.github_repo.get_release(id=identifier)
        return GithubRelease(release, project)

    @staticmethod
    def get_latest(project: "ogr_github.GithubProject") -> Optional["Release"]:
        try:
            release = project.github_repo.get_latest_release()
            return GithubRelease(release, project)
        except GithubException as ex:
            if ex.status == 404:
                return None
            raise GithubAPIException from ex

    @staticmethod
    def get_list(project: "ogr_github.GithubProject") -> list["Release"]:
        releases = project.github_repo.get_releases()
        return [GithubRelease(release, project) for release in releases]

    @staticmethod
    def create(
        project: "ogr_github.GithubProject",
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "Release":
        created_release = project.github_repo.create_git_release(
            tag=tag,
            name=name,
            message=message,
        )
        return GithubRelease(created_release, project)

    def edit_release(self, name: str, message: str) -> None:
        """
        Edit name and message of a release.

        Args:
            name: New name of the release.
            message: New message for the release.
        """
        self._raw_release = self._raw_release.update_release(name=name, message=message)

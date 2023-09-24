# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import Optional

from gitlab.v4.objects import ProjectRelease as _GitlabRelease

from ogr.abstract import GitTag, Release
from ogr.exceptions import OperationNotSupported
from ogr.services import gitlab as ogr_gitlab


class GitlabRelease(Release):
    _raw_release: _GitlabRelease
    project: "ogr_gitlab.GitlabProject"

    @property
    def title(self):
        return self._raw_release.name

    @property
    def body(self):
        return self._raw_release.description

    @property
    def git_tag(self) -> GitTag:
        return self.project._git_tag_from_tag_name(self.tag_name)

    @property
    def tag_name(self) -> str:
        return self._raw_release.tag_name

    @property
    def url(self) -> Optional[str]:
        return f"{self.project.get_web_url()}/-/releases/{self.tag_name}"

    @property
    def created_at(self) -> datetime.datetime:
        return self._raw_release.created_at

    @property
    def tarball_url(self) -> str:
        return self._raw_release.assets["sources"][1]["url"]

    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

    @staticmethod
    def get(
        project: "ogr_gitlab.GitlabProject",
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "Release":
        release = project.gitlab_repo.releases.get(tag_name)
        return GitlabRelease(release, project)

    @staticmethod
    def get_latest(project: "ogr_gitlab.GitlabProject") -> Optional["Release"]:
        releases = project.gitlab_repo.releases.list()
        # list of releases sorted by released_at
        return GitlabRelease(releases[0], project) if releases else None

    @staticmethod
    def get_list(project: "ogr_gitlab.GitlabProject") -> list["Release"]:
        if not hasattr(project.gitlab_repo, "releases"):
            raise OperationNotSupported(
                "This version of python-gitlab does not support release, please upgrade.",
            )
        releases = project.gitlab_repo.releases.list(all=True)
        return [GitlabRelease(release, project) for release in releases]

    @staticmethod
    def create(
        project: "ogr_gitlab.GitlabProject",
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "Release":
        release = project.gitlab_repo.releases.create(
            {"name": name, "tag_name": tag, "description": message, "ref": ref},
        )
        return GitlabRelease(release, project)

    def edit_release(self, name: str, message: str) -> None:
        raise OperationNotSupported("edit_release not supported on GitLab")

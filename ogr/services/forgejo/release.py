# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from dataclasses import dataclass
from typing import Any, Optional

from pyforgejo import PyforgejoApi

from ogr.abstract import GitProject, Release
from ogr.abstract import GitTag as AbstractGitTag
from ogr.abstract import Release as AbstractRelease


@dataclass
class ForgejoProject(GitProject):
    api: PyforgejoApi


class ForgejoGitTag(AbstractGitTag):
    """
    Concrete implementation of GitTag for Forgejo
    """

    def __init__(self, name: str, commit_sha: str) -> None:
        self.name = name
        self.commit_sha = commit_sha

    def __str__(self) -> str:
        return f"GitTag(name={self.name}, commit_sha={self.commit_sha})"


class ForgejoRelease(AbstractRelease):
    """
    Concrete implementation of Release for Forgejo.
    """

    def __init__(self, raw_release: dict, project: ForgejoProject):
        self._raw_release = raw_release
        self.project: ForgejoProject = project

    @property
    def title(self) -> str:
        return self._raw_release.get("name", "")

    @property
    def body(self) -> str:
        return self._raw_release.get("description", "")

    @property
    def git_tag(self) -> AbstractGitTag:
        return ForgejoGitTag(self.tag_name, self._raw_release.get("commit_sha", ""))

    @property
    def tag_name(self) -> str:
        return self._raw_release.get("tag_name", "")

    @property
    def url(self) -> Optional[str]:
        return self._raw_release.get("html_url")

    @property
    def created_at(self) -> datetime.datetime:
        created_value = self._raw_release.get("created_at")
        if isinstance(created_value, datetime.datetime):
            return created_value
        return (
            datetime.datetime.strptime(created_value, "%Y-%m-%dT%H:%M:%SZ")
            if created_value
            else datetime.datetime.now()
        )

    @property
    def tarball_url(self) -> str:
        return self._raw_release.get("tarball_url", "")

    @staticmethod
    def get(
        project: ForgejoProject,
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "ForgejoRelease":
        params: dict[str, int | str] = {}
        if identifier is not None:
            params["id"] = identifier
        if name is not None:
            params["name"] = name
        if tag_name is not None:
            params["tag"] = tag_name
        releases = project.api.get_releases(
            owner=project.owner,
            repo=project.repo,
            params=params,
        )
        return ForgejoRelease(releases[0], project)

    @staticmethod
    def get_latest(project: Any) -> Optional["ForgejoRelease"]:
        try:
            release_data = project.api.get_latest_release(
                owner=project.owner,
                repo=project.repo,
            )
            return ForgejoRelease(release_data, project)
        except Exception:
            return None

    @staticmethod
    def get_list(project: Any) -> list["ForgejoRelease"]:
        releases_data = project.api.repo_list_releases(
            owner=project.owner,
            repo=project.repo,
        )
        return [ForgejoRelease(release, project) for release in releases_data]

    @staticmethod
    def create(
        project: ForgejoProject,
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "Release":
        release_data = project.api.repo_create_release(
            owner=project.owner,
            repo=project.repo,
            tag_name=tag,
            name=name,
            body=message,
            target_commitish=ref,
            draft=False,
            prerelease=False,
        )
        return ForgejoRelease(release_data, project)

    def edit_release(self, name: str, message: str) -> None:
        payload = {"name": name, "body": message}
        release_data = self.project.api.edit_release(
            owner=self.project.owner,
            repo=self.project.repo,
            tag=self.tag_name,
            payload=payload,
        )
        self._raw_release = release_data

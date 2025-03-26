# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import Any, Optional

from pyforgejo import PyforgejoApi


class GitTag:
    """
    Class representing a git tag.

    Attributes:
        name (str): Name of the tag.
        commit_sha (str): Commit hash of the tag.
    """

    def __init__(self, name: str, commit_sha: str) -> None:
        self.name = name
        self.commit_sha = commit_sha

    def __str__(self) -> str:
        return f"GitTag(name={self.name}, commit_sha={self.commit_sha})"


class ForgejoGitTag(GitTag):
    """
    Concrete implementation of GitTag for Forgejo.
    """

    # Using the base implementation as no additional functionality is needed.


class Release:
    """
    Object that represents a release.
    """

    def __init__(self, raw_release: Any, project: Any) -> None:
        self._raw_release = raw_release
        self.project = project


class ForgejoRelease(Release):
    """
    Concrete implementation of Release for Forgejo.
    """

    @property
    def title(self) -> str:
        return self._raw_release.get("name", "")

    @property
    def body(self) -> str:
        return self._raw_release.get("description", "")

    @property
    def git_tag(self) -> GitTag:
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
        project: Any,
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "Release":
        client = PyforgejoApi(api_url=project.forge_api_url, token=project.token)
        params: dict[str, int | str] = {}
        if identifier is not None:
            params["id"] = identifier
        if name is not None:
            params["name"] = name
        if tag_name is not None:
            params["tag"] = tag_name
        release_data = client.get_releases(
            owner=project.owner,
            repo=project.repo,
            params=params,
        )
        return ForgejoRelease(release_data, project)

    @staticmethod
    def get_latest(project: Any) -> Optional["Release"]:
        client = PyforgejoApi(api_url=project.forge_api_url, token=project.token)
        try:
            release_data = client.get_latest_release(
                owner=project.owner,
                repo=project.repo,
            )
            return ForgejoRelease(release_data, project)
        except Exception:
            return None

    @staticmethod
    def get_list(project: Any) -> list["Release"]:
        client = PyforgejoApi(api_url=project.forge_api_url, token=project.token)
        releases_data = client.get_releases(owner=project.owner, repo=project.repo)
        return [ForgejoRelease(release, project) for release in releases_data]

    @staticmethod
    def create(
        project: Any,
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "ForgejoRelease":
        client = PyforgejoApi(api_url=project.forge_api_url, token=project.token)
        payload = {
            "tag_name": tag,
            "name": name,
            "body": message,
            "target_commitish": ref,
        }
        release_data = client.create_release(
            owner=project.owner,
            repo=project.repo,
            payload=payload,
        )
        return ForgejoRelease(release_data, project)

    def save_archive(self, filename: str) -> None:
        tarball_url = self.tarball_url
        if not tarball_url:
            raise ValueError("Tarball URL is not available")
        client = PyforgejoApi(
            api_url=self.project.forge_api_url,
            token=self.project.token,
        )
        # Assume the SDK provides a method to download the tarball.
        content = client.download_tarball(url=tarball_url)
        with open(filename, "wb") as f:
            f.write(content)

    def edit_release(self, name: str, message: str) -> None:
        client = PyforgejoApi(
            api_url=self.project.forge_api_url,
            token=self.project.token,
        )
        payload = {"name": name, "body": message}
        release_data = client.edit_release(
            owner=self.project.owner,
            repo=self.project.repo,
            tag=self.tag_name,
            payload=payload,
        )
        self._raw_release = release_data

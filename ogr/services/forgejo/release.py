# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import Any, Optional

import requests


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
    Object that represents release.
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
        created_str = self._raw_release.get("created_at", "")
        return (
            datetime.datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%SZ")
            if created_str
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
        url = f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/releases"
        params: dict[str, int | str] = {}
        if identifier is not None:
            params["id"] = identifier
        if name is not None:
            params["name"] = name
        if tag_name is not None:
            params["tag"] = tag_name
        headers = project.get_auth_header()
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return ForgejoRelease(response.json(), project)

    @staticmethod
    def get_latest(project: Any) -> Optional["Release"]:
        url = f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/releases/latest"
        headers = project.get_auth_header()
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        return ForgejoRelease(response.json(), project)

    @staticmethod
    def get_list(project: Any) -> list["Release"]:
        url = f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/releases"
        headers = project.get_auth_header()
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return [ForgejoRelease(release, project) for release in response.json()]

    @staticmethod
    def create(
        project: Any,
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "ForgejoRelease":
        url = f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/releases"
        payload = {
            "tag_name": tag,
            "name": name,
            "body": message,
            "target_commitish": ref,
        }
        headers = project.get_auth_header()
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return ForgejoRelease(response.json(), project)

    def save_archive(self, filename: str) -> None:
        tarball_url = self.tarball_url
        if not tarball_url:
            raise ValueError("Tarball URL is not available")
        headers = self.project.get_auth_header()
        response = requests.get(tarball_url, headers=headers)
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)

    def edit_release(self, name: str, message: str) -> None:
        url = (
            f"{self.project.forge_api_url}/repos/{self.project.owner}/"
            f"{self.project.repo}/releases/{self.tag_name}"
        )
        payload = {"name": name, "body": message}
        headers = self.project.get_auth_header()
        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()
        self._raw_release = response.json()

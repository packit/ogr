# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from collections.abc import Iterable
from typing import Any, Optional, Union

from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.git_project import GitProject
from ogr.abstract.git_tag import GitTag


class Release(OgrAbstractClass):
    """
    Object that represents release.

    Attributes:
        project (GitProject): Project on which the release is created.
    """

    def __init__(
        self,
        raw_release: Any,
        project: "GitProject",
    ) -> None:
        self._raw_release = raw_release
        self.project = project

    def __str__(self) -> str:
        return (
            f"Release("
            f"title='{self.title}', "
            f"body='{self.body}', "
            f"tag_name='{self.tag_name}', "
            f"url='{self.url}', "
            f"created_at='{self.created_at}', "
            f"tarball_url='{self.tarball_url}')"
        )

    @property
    def title(self) -> str:
        """Title of the release."""
        raise NotImplementedError()

    @property
    def body(self) -> str:
        """Body of the release."""
        raise NotImplementedError()

    @property
    def git_tag(self) -> GitTag:
        """Object that represents tag tied to the release."""
        raise NotImplementedError()

    @property
    def tag_name(self) -> str:
        """Tag tied to the release."""
        raise NotImplementedError()

    @property
    def url(self) -> Optional[str]:
        """URL of the release."""
        raise NotImplementedError()

    # TODO: Check if should really be string
    @property
    def created_at(self) -> datetime.datetime:
        """Datetime of creating the release."""
        raise NotImplementedError()

    @property
    def tarball_url(self) -> str:
        """URL of the tarball."""
        raise NotImplementedError()

    @staticmethod
    def get(
        project: Any,
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "Release":
        """
        Get a single release.

        Args:
            identifier: Identifier of the release.

                Defaults to `None`, which means not being used.
            name: Name of the release.

                Defaults to `None`, which means not being used.
            tag_name: Tag that the release is tied to.

                Defaults to `None`, which means not being used.

        Returns:
            Object that represents release that satisfies requested condition.
        """
        raise NotImplementedError()

    @staticmethod
    def get_latest(project: Any) -> Optional["Release"]:
        """
        Returns:
            Object that represents the latest release.
        """
        raise NotImplementedError()

    @staticmethod
    def get_list(project: Any) -> Union[list["Release"], Iterable["Release"]]:
        """
        Returns:
            List of the objects that represent releases.
        """
        raise NotImplementedError()

    @staticmethod
    def create(
        project: Any,
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "Release":
        """
        Create new release.

        Args:
            project: Project where the release is to be created.
            tag: Tag which is the release based off.
            name: Name of the release.
            message: Message or description of the release.
            ref: Git reference, mainly commit hash for the release. If provided
                git tag is created prior to creating a release.

                Defaults to `None`.

        Returns:
            Object that represents newly created release.
        """
        raise NotImplementedError()

    def save_archive(self, filename: str) -> None:
        """
        Save tarball of the release to requested `filename`.

        Args:
            filename: Path to the file to save archive to.
        """
        raise NotImplementedError()

    def edit_release(self, name: str, message: str) -> None:
        """
        Edit name and message of a release.

        Args:
            name: Name of the release.
            message: Description of the release.
        """
        raise NotImplementedError()

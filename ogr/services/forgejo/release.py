# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
import datetime
from functools import cached_property, partial
from typing import Optional

from pyforgejo.types import Release as PyforgejoRelease

from ogr.abstract import GitTag, Release
from ogr.exceptions import ForgejoAPIException
from ogr.services import forgejo as ogr_forgejo
from ogr.services.forgejo.utils import paginate


class ForgejoRelease(Release):
    _raw_release: PyforgejoRelease
    project: "ogr_forgejo.ForgejoProject"

    @property
    def title(self) -> str:
        return self._raw_release.name

    @property
    def body(self) -> str:
        return self._raw_release.body

    @cached_property
    def git_tag(self) -> GitTag:
        tag = self.project.api.repo_get_tag(
            owner=self.project.namespace,
            repo=self.project.repo,
            tag=self.tag_name,
        )
        return GitTag(name=tag.name, commit_sha=tag.commit.sha)

    @property
    def tag_name(self) -> str:
        return self._raw_release.tag_name

    @property
    def url(self) -> Optional[str]:
        return self._raw_release.url

    @property
    def created_at(self) -> datetime.datetime:
        return self._raw_release.created_at

    @property
    def tarball_url(self) -> str:
        return self._raw_release.tarball_url

    @staticmethod
    def _release_id_from_name(
        project: "ogr_forgejo.ForgejoProject",
        name: str,
    ) -> Optional[int]:
        for release in paginate(
            partial(
                project.api.repo_list_releases,
                owner=project.namespace,
                repo=project.repo,
            ),
        ):
            if release.name == name:
                return release.id
        return None

    @staticmethod
    def get(
        project: "ogr_forgejo.ForgejoProject",
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "Release":
        if tag_name:
            release = project.api.repo_get_release_by_tag(
                owner=project.namespace,
                repo=project.repo,
                tag=tag_name,
            )
            return ForgejoRelease(release, project)

        if name:
            identifier = ForgejoRelease._release_id_from_name(project, name)

        if identifier is None:
            raise ForgejoAPIException("Release was not found.")

        release = project.api.repo_get_release(
            owner=project.namespace,
            repo=project.repo,
            id=identifier,
        )
        return ForgejoRelease(release, project)

    @staticmethod
    def get_latest(project: "ogr_forgejo.ForgejoProject") -> Optional["Release"]:
        releases = project.api.repo_list_releases(
            owner=project.namespace,
            repo=project.repo,
            page=1,
            limit=1,
        )

        return ForgejoRelease(releases[0], project) if releases else None

    @staticmethod
    def get_list(project: "ogr_forgejo.ForgejoProject") -> list["Release"]:
        releases = paginate(
            partial(
                project.api.repo_list_releases,
                owner=project.namespace,
                repo=project.repo,
            ),
        )
        return [ForgejoRelease(release, project) for release in releases]

    @staticmethod
    def create(
        project: "ogr_forgejo.ForgejoProject",
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "Release":
        release = project.api.repo_create_release(
            owner=project.namespace,
            repo=project.repo,
            tag_name=tag,
            body=message,
            name=name,
            target_commitish=ref,
        )

        return ForgejoRelease(release, project)

    def edit_release(self, name: str, message: str) -> None:
        try:
            data = {}
            if name is not None:
                data["name"] = name

            if message is not None:
                data["body"] = message

            updated_release = self.project.api.repo_edit_release(
                owner=self.project.namespace,
                repo=self.project.repo,
                id=self._raw_release.id,
                **data,
            )

            self._raw_release = updated_release
        except Exception as ex:
            raise ForgejoAPIException(
                f"There was an error while updating Forgejo release: {ex}",
            ) from ex

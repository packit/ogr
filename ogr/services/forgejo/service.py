# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from functools import cached_property
from typing import Optional
from urllib.parse import urlparse

from pyforgejo import PyforgejoApi

from ogr.abstract import GitUser
from ogr.exceptions import OgrException
from ogr.factory import use_for_service
from ogr.services.base import BaseGitService
from ogr.services.forgejo.project import ForgejoProject
from ogr.services.forgejo.user import ForgejoUser


@use_for_service("forgejo")
@use_for_service("codeberg.org")
class ForgejoService(BaseGitService):
    version = "/api/v1"

    def __init__(
        self,
        instance_url: str = "https://codeberg.org",
        api_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__()
        self.instance_url = instance_url + self.version
        self._token = f"token {api_key}"
        self._api = None

    @cached_property
    def api(self):
        return PyforgejoApi(base_url=self.instance_url, api_key=self._token)

    def get_project(  # type: ignore[override]
        self,
        repo: str,
        namespace: str,
        **kwargs,
    ) -> "ForgejoProject":
        return ForgejoProject(
            repo=repo,
            namespace=namespace,
            service=self,
            **kwargs,
        )

    @property
    def user(self) -> GitUser:
        return ForgejoUser(self)

    def project_create(
        self,
        repo: str,
        namespace: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "ForgejoProject":
        if namespace:
            new_repo = self.api.organization.create_org_repo(
                org=namespace,
                name=repo,
                description=description,
            )
        else:
            new_repo = self.api.repository.create_current_user_repo(
                name=repo,
                description=description,
            )
        return ForgejoProject(
            repo=repo,
            namespace=namespace,
            service=self,
            github_repo=new_repo,
        )

    def get_project_from_url(self, url: str) -> "ForgejoProject":
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")

        if len(path_parts) < 2:
            raise OgrException(f"Invalid Forgejo URL: {url}")

        namespace = path_parts[0]
        repo = path_parts[1]

        return self.get_project(repo=repo, namespace=namespace)

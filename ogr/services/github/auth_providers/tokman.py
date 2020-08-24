# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import requests
from typing import Optional

import github

from ogr.services.github.auth_providers.abstract import GithubAuthentication
from ogr.exceptions import OgrException


class Tokman(GithubAuthentication):
    def __init__(self, instance_url: str):
        self._instance_url = instance_url

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, Tokman):
            return False

        return self._instance_url == o._instance_url  # type: ignore

    def __str__(self) -> str:
        return f"Tokman(instance_url='{self._instance_url}')"

    @property
    def pygithub_instance(self) -> Optional[github.Github]:
        # used for backward compatibility with GitUser
        return None

    def get_token(self, namespace: str, repo: str) -> str:
        response = requests.get(f"{self._instance_url}/api/{namespace}/{repo}")

        if not response.ok:
            raise OgrException(
                f"Couldn't retrieve token from Tokman: ({response.status_code}) {response.text}"
            )

        return response.json().get("access_token", None)

    @staticmethod
    def try_create(tokman_instance_url: str = None, **_) -> Optional["Tokman"]:
        return Tokman(tokman_instance_url) if tokman_instance_url else None

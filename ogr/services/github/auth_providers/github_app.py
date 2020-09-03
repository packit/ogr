# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import Optional

import github

from ogr.services.github.auth_providers.abstract import GithubAuthentication
from ogr.exceptions import OgrException


class GithubApp(GithubAuthentication):
    def __init__(self, id: str, private_key: str, private_key_path: str) -> None:
        self.id = id
        self._private_key = private_key
        self._private_key_path = private_key_path

        self._github: github.Github = None
        self._integration: github.GithubIntegration = None

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, GithubApp):
            return False

        return (
            self.id == o.id  # type: ignore
            and self._private_key == o._private_key  # type: ignore
            and self._private_key_path == o._private_key_path  # type: ignore
        )

    def __str__(self) -> str:
        censored_id = f"id='{self.id[:1]}***{self.id[-1:]}'"
        censored_private_key = (
            f", private_key" f"='{self._private_key[:1]}***{self._private_key[-1:]}'"
            if self._private_key
            else ""
        )
        private_key_path = (
            f", private_key_path='{self._private_key_path}'"
            if self._private_key_path
            else ""
        )

        return f"GithubApp({censored_id}{censored_private_key}{private_key_path})"

    @property
    def private_key(self) -> str:
        if self._private_key:
            return self._private_key

        if self._private_key_path:
            if not Path(self._private_key_path).is_file():
                raise OgrException(
                    f"File with the github-app private key "
                    f"({self._private_key_path}) "
                    f"does not exist."
                )
            return Path(self._private_key_path).read_text()

        return None

    @property
    def pygithub_instance(self) -> Optional[github.Github]:
        # used for backward compatibility with GitUser
        return None

    @property
    def integration(self) -> github.GithubIntegration:
        if not self._integration:
            self._integration = github.GithubIntegration(self.id, self.private_key)
        return self._integration

    def get_token(self, namespace: str, repo: str) -> str:
        if not self.private_key:
            return None

        inst_id = self.integration.get_installation(namespace, repo).id
        # PyGithub<1.52 returned an object for id, with a value attribute,
        # which was None or an ID.
        # This was changed in:
        # https://github.com/PyGithub/PyGithub/commit/61808da15e8e3bcb660acd0e7947326a4a6c0c7a#diff-b8f1ee87df332916352809a397ea259aL54
        # 'id' is now None or an ID.
        inst_id = (
            inst_id
            if isinstance(inst_id, int) or inst_id is None
            else inst_id.value  # type: ignore
        )
        if not inst_id:
            raise OgrException(
                f"No installation ID provided for {namespace}/{repo}: "
                "please make sure that you provided correct credentials of your GitHub app."
            )
        inst_auth = self.integration.get_access_token(inst_id)  # type: ignore
        return inst_auth.token

    @staticmethod
    def try_create(
        github_app_id: str = None,
        github_app_private_key: str = None,
        github_app_private_key_path: str = None,
        **_,
    ) -> Optional["GithubApp"]:
        return (
            GithubApp(
                github_app_id, github_app_private_key, github_app_private_key_path
            )
            if github_app_id
            else None
        )

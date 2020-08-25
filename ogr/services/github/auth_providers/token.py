# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

import github

from ogr.services.github.auth_providers.abstract import GithubAuthentication


class TokenAuthentication(GithubAuthentication):
    def __init__(self, token: str, **_) -> None:
        self._token = token
        self._pygithub_instance = github.Github(login_or_token=token)

    def __eq__(self, o: object) -> bool:
        return issubclass(o.__class__, TokenAuthentication) and (
            self._token == o._token  # type: ignore
        )

    def __str__(self) -> str:
        censored_token = (
            f"token='{self._token[:1]}***{self._token[-1:]}'" if self._token else ""
        )
        return f"Token({censored_token})"

    @property
    def pygithub_instance(self) -> github.Github:
        return self._pygithub_instance

    def get_token(self, namespace: str, repo: str) -> str:
        return self._token

    @staticmethod
    def try_create(token: str = None, **_) -> Optional["TokenAuthentication"]:
        return TokenAuthentication(token)

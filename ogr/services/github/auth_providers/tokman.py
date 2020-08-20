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
        self.__healthy = False

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, Tokman):
            return False

        return self._instance_url == o._instance_url  # type: ignore

    def __str__(self) -> str:
        # TODO: Check if needs to be censored
        return f"Tokman(instance_url='{self._instance_url}')"

    @property
    def pygithub_instance(self) -> github.Github:
        return github.Github()

    def _check_tokman_instance(self):
        try:
            # check if running correctly
            health = requests.get(f"{self._instance_url}/api/health")

            if not health.ok or health.json().get("message", None) != "ok":
                raise OgrException("Tokman instance is not running")
        except OgrException as ex:
            raise ex
        except Exception as ex:
            raise OgrException(f"Couldn't connect to Tokman instance: {ex}")

        self.__running = True

    def get_pygithub_instance(self, namespace: str, repo: str) -> github.Github:
        if not self.__running:
            self._check_tokman_instance()

        response = requests.get(f"{self._instance_url}/api/{namespace}/{repo}")

        json_response = response.json()
        token = json_response.get("access_token", None)

        if not response.ok or not token:
            # haven't managed to get a token
            error = json_response.get("error", "no message provided")
            raise OgrException(f"Couldn't retrieve token from Tokman: {error}")

        return github.Github(login_or_token=token)

    @staticmethod
    def try_create(tokman_instance_url: str = None, **_) -> Optional["Tokman"]:
        return Tokman(tokman_instance_url) if tokman_instance_url else None

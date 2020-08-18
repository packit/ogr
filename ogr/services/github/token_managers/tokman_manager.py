# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


import requests


import github


from ogr.abstract import GithubTokenManager
from ogr.exceptions import OgrException


class TokmanGithubTokenManager(GithubTokenManager):
    def __init__(self, instance_url: str):
        self.__instance_url = instance_url

        try:
            # check if running correctly
            health = requests.get(f"{self.__instance_url}/api/health")

            if not health.ok or health.json().get("message", None) != "ok":
                raise OgrException("Tokman instance is not running")
        except OgrException as ex:
            raise ex
        except Exception as ex:
            raise OgrException(f"Couldn't connect to Tokman instance: {ex}")

    def get_pygithub_instance(self, namespace: str, repo: str) -> github.Github:
        response = requests.get(f"{self.__instance_url}/api/{namespace}/{repo}")

        json_response = response.json()
        token = json_response.get("access_token", None)

        if not response.ok or not token:
            # haven't managed to get a token
            error = json_response.get("error", "no message provided")
            raise OgrException(f"Couldn't retrieve token from Tokman: {error}")

        return github.Github(login_or_token=token)

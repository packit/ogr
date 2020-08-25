# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

import github


class GithubAuthentication:
    """
    Represents a token manager for authentication via GitHubApp.
    """

    def get_token(self, namespace: str, repo: str) -> str:
        """
        Returns GitHub token for a requested repository.

        :param namespace: namespace of the repository
        :param repo: name of the repository
        :return: token that can be used in PyGithub instance for authentication
        """
        raise NotImplementedError()

    @property
    def pygithub_instance(self) -> "github.Github":
        """
        Returns generic PyGithub instance. Used for `GitUser` for example.
        """
        raise NotImplementedError()

    @staticmethod
    def try_create(**kwargs) -> Optional["GithubAuthentication"]:
        """
        Tries to construct authentication object from provided keyword arguments.
        :return: None if unsuccessful
        """
        raise NotImplementedError()

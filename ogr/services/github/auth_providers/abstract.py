# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

import github


class GithubAuthentication:
    """
    Represents a token manager for authentication via GitHubApp.
    """

    def get_pygithub_instance(self, namespace: str, repo: str) -> github.Github:
        """
        Returns GitHub instance for a requested repository,
        authenticated using GitHub App

        :param namespace: namespace of the repository
        :param repo: name of the repository
        :return: instance of github.Github
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

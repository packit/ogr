# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional

import github


class GithubAuthentication:
    """
    Represents a token manager for authentication via GitHub App.
    """

    def get_token(self, namespace: str, repo: str) -> str:
        """
        Get a GitHub token for requested repository.

        Args:
            namespace: Namespace of the repository.
            repo: Name of the repository.

        Returns:
            A token that can be used in PyGithub instance for authentication.
        """
        raise NotImplementedError()

    @property
    def pygithub_instance(self) -> "github.Github":
        """
        Returns:
            Generic PyGithub instance. Used for `GitUser` for example.
        """
        raise NotImplementedError()

    @staticmethod
    def try_create(**kwargs) -> Optional["GithubAuthentication"]:
        """
        Tries to construct authentication object from provided keyword arguments.

        Returns:
            `GithubAuthentication` object or `None` if the creation was not
            successful.
        """
        raise NotImplementedError()

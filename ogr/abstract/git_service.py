# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from typing import Any, Optional, Union

from ogr import abstract as _abstract
from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.auth_method import AuthMethod
from ogr.abstract.git_project import GitProject
from ogr.exceptions import OgrException
from ogr.parsing import parse_git_repo

try:
    from functools import cached_property as _cached_property  # type: ignore
except ImportError:
    from functools import lru_cache

    def _cached_property(func):  # type: ignore
        return property(lru_cache()(func))


class GitService(OgrAbstractClass):
    """
    Attributes:
        instance_url (str): URL of the git forge instance.
    """

    instance_url: Optional[str] = None

    def __init__(self, **_: Any) -> None:
        pass

    def __str__(self) -> str:
        return f"GitService(instance_url={self.instance_url})"

    def get_project(self, **kwargs: Any) -> "GitProject":
        """
        Get the requested project.

        Args:
            namespace (str): Namespace of the project.
            user (str): Username of the project's owner.
            repo (str): Repository name.

        Returns:
            Object that represents git project.
        """
        raise NotImplementedError

    def get_project_from_url(self, url: str) -> "GitProject":
        """
        Args:
            url: URL of the git repository.

        Returns:
            Object that represents project from the parsed URL.
        """
        repo_url = parse_git_repo(potential_url=url)
        if not repo_url:
            raise OgrException(f"Failed to find repository for url: {url}")
        return self.get_project(repo=repo_url.repo, namespace=repo_url.namespace)

    @_cached_property
    def hostname(self) -> Optional[str]:
        """Hostname of the service."""
        raise NotImplementedError

    @property
    def user(self) -> "_abstract.GitUser":
        """User authenticated through the service."""
        raise NotImplementedError

    def change_token(self, new_token: str) -> None:
        """
        Change an API token. Only for the current instance and newly created projects.

        Args:
            new_token: New token to be set.
        """
        raise NotImplementedError

    def set_auth_method(self, method: AuthMethod) -> None:
        """
        Override the default auth method.
        Can be used when the service has more auth methods available.

        Args:
            method: the method identifier (a str name)
        """
        raise NotImplementedError()

    def reset_auth_method(self) -> None:
        """
        Set the auth method to the default one.
        """
        raise NotImplementedError()

    def project_create(
        self,
        repo: str,
        namespace: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "GitProject":
        """
        Create new project.

        Args:
            repo: Name of the newly created project.
            namespace: Namespace of the newly created project.

                Defaults to currently authenticated user.
            description: Description of the newly created project.

        Returns:
            Object that represents newly created project.
        """
        raise NotImplementedError()

    def list_projects(
        self,
        namespace: Optional[str] = None,
        user: Optional[str] = None,
        search_pattern: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Union[list["GitProject"], Iterable["GitProject"]]:
        """
        List projects for given criteria.

        Args:
            namespace: Namespace to list projects from.
            user: Login of the owner of the projects.
            search_pattern: Regular expression that repository name should match.
            language: Language to be present in the project, e.g. `"python"` or
                `"html"`.
        """
        raise NotImplementedError

    def get_group(self, group_name: str):
        """
        Get a group by name.
        """
        raise NotImplementedError

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging
from typing import Optional, Type, Union, List, Dict

import re
from urllib3.util import Retry
import github
import github.GithubObject
from github import (
    UnknownObjectException,
    Github as PyGithubInstance,
    Repository as PyGithubRepository,
)

from ogr.abstract import GitUser, AuthMethod
from ogr.exceptions import GithubAPIException
from ogr.factory import use_for_service
from ogr.services.base import BaseGitService, GitProject
from ogr.services.github.project import GithubProject
from ogr.services.github.auth_providers import (
    GithubAuthentication,
    TokenAuthentication,
    GithubApp,
    Tokman,
)
from ogr.services.github.user import GithubUser

logger = logging.getLogger(__name__)


@use_for_service("github.com")
class GithubService(BaseGitService):
    # class parameter could be used to mock Github class api
    github_class: Type[github.Github]
    instance_url = "https://github.com"

    def __init__(
        self,
        token=None,
        read_only=False,
        github_app_id: str = None,
        github_app_private_key: str = None,
        github_app_private_key_path: str = None,
        tokman_instance_url: str = None,
        github_authentication: GithubAuthentication = None,
        max_retries: Union[int, Retry] = 0,
        **kwargs,
    ):
        """
        If multiple authentication methods are provided, they are prioritised:
            1. Tokman
            2. GithubApp
            3. TokenAuthentication (which is also default one, that works without specified token)
        """
        super().__init__()
        self.read_only = read_only
        self._default_auth_method = github_authentication
        self._other_auth_method: GithubAuthentication = None
        self._auth_methods: Dict[AuthMethod, GithubAuthentication] = {}

        if isinstance(max_retries, Retry):
            self._max_retries = max_retries
        else:
            self._max_retries = Retry(
                total=int(max_retries),
                read=0,
                # Retry mechanism active for these HTTP methods:
                allowed_methods=["DELETE", "GET", "PATCH", "POST", "PUT"],
                # Only retry on following HTTP status codes
                status_forcelist=[500, 503, 403, 401],
                raise_on_status=False,
            )

        if not self._default_auth_method:
            self.__set_authentication(
                token=token,
                github_app_id=github_app_id,
                github_app_private_key=github_app_private_key,
                github_app_private_key_path=github_app_private_key_path,
                tokman_instance_url=tokman_instance_url,
                max_retries=self._max_retries,
            )

        if kwargs:
            logger.warning(f"Ignored keyword arguments: {kwargs}")

    def __set_authentication(self, **kwargs):
        auth_methods = [
            (Tokman, AuthMethod.tokman),
            (GithubApp, AuthMethod.github_app),
            (TokenAuthentication, AuthMethod.token),
        ]
        for auth_class, auth_name in auth_methods:
            auth_inst = auth_class.try_create(**kwargs)
            self._auth_methods[auth_name] = auth_inst
            if not self._default_auth_method:
                self._default_auth_method = auth_inst

        return None if self._default_auth_method else TokenAuthentication(None)

    def set_auth_method(self, method: AuthMethod):
        if self._auth_methods[method]:
            logger.info("Forced Github auth method to %s", method)
            self._other_auth_method = self._auth_methods[method]
        else:
            raise GithubAPIException(
                f"Choosen authentication method ({method}) is not available"
            )

    def reset_auth_method(self):
        logger.info("Reset Github auth method to the default")
        self._other_auth_method = None

    @property
    def authentication(self):
        return self._other_auth_method or self._default_auth_method

    @property
    def github(self):
        return self.authentication.pygithub_instance

    def __str__(self) -> str:
        readonly_str = ", read_only=True" if self.read_only else ""
        arguments = f", github_authentication={str(self.authentication)}{readonly_str}"

        if arguments:
            # remove the first '- '
            arguments = arguments[2:]

        return f"GithubService({arguments})"

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, GithubService):
            return False

        return (
            self.read_only == o.read_only  # type: ignore
            and self.authentication == o.authentication  # type: ignore
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def get_project(
        self, repo=None, namespace=None, is_fork=False, **kwargs
    ) -> "GithubProject":
        if is_fork:
            namespace = self.user.get_username()
        return GithubProject(
            repo=repo,
            namespace=namespace,
            service=self,
            read_only=self.read_only,
            **kwargs,
        )

    def get_project_from_github_repository(
        self, github_repo: PyGithubRepository.Repository
    ) -> "GithubProject":
        return GithubProject(
            repo=github_repo.name,
            namespace=github_repo.owner.login,
            github_repo=github_repo,
            service=self,
            read_only=self.read_only,
        )

    @property
    def user(self) -> GitUser:
        return GithubUser(service=self)

    def change_token(self, new_token: str) -> None:
        self._default_auth_method = TokenAuthentication(new_token)

    def project_create(
        self,
        repo: str,
        namespace: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "GithubProject":
        if namespace:
            try:
                owner = self.github.get_organization(namespace)
            except UnknownObjectException as ex:
                raise GithubAPIException(f"Group {namespace} not found.") from ex
        else:
            owner = self.github.get_user()

        try:
            new_repo = owner.create_repo(
                name=repo,
                description=description if description else github.GithubObject.NotSet,
            )
        except github.GithubException as ex:
            raise GithubAPIException("Project creation failed") from ex
        return GithubProject(
            repo=repo,
            namespace=namespace or owner.login,
            service=self,
            github_repo=new_repo,
        )

    def get_pygithub_instance(self, namespace: str, repo: str) -> PyGithubInstance:
        token = None
        if self.authentication:
            token = self.authentication.get_token(namespace, repo)
        return PyGithubInstance(login_or_token=token, retry=self._max_retries)

    def list_projects(
        self,
        namespace: str = None,
        user: str = None,
        search_pattern: str = None,
        language: str = None,
    ) -> List[GitProject]:
        search_query = ""

        if user:
            search_query += f"user:{user}"

        if language:
            search_query += f" language:{language}"

        projects: List[GitProject]
        projects = [
            GithubProject(
                repo=repo.name,
                namespace=repo.owner.login,
                github_repo=repo,
                service=self,
            )
            for repo in self.github.search_repositories(search_query, order="asc")
        ]

        if search_pattern:
            projects = [
                project
                for project in projects
                if re.search(search_pattern, project.repo)
            ]

        return projects

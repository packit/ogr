# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
from typing import Optional, Type, Union, List

import re
from urllib3.util import Retry
import github
import github.GithubObject
from github import (
    UnknownObjectException,
    Github as PyGithubInstance,
    Repository as PyGithubRepository,
)

from ogr.abstract import GitUser
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
        self.authentication = github_authentication

        if isinstance(max_retries, Retry):
            self._max_retries = max_retries
        else:
            self._max_retries = Retry(
                total=int(max_retries),
                read=0,
                # Retry mechanism active for these HTTP methods:
                method_whitelist=["DELETE", "GET", "PATCH", "POST", "PUT"],
                # Only retry on following HTTP status codes
                status_forcelist=[500, 503, 403, 401],
                raise_on_status=False,
            )

        if not self.authentication:
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
            Tokman,
            GithubApp,
            TokenAuthentication,
        ]
        for auth_class in auth_methods:
            self.authentication = auth_class.try_create(**kwargs)
            if self.authentication:
                return

        return TokenAuthentication(None)

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
        self.authentication = TokenAuthentication(new_token)

    def project_create(
        self,
        repo: str,
        namespace: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "GithubProject":
        if namespace:
            try:
                owner = self.github.get_organization(namespace)
            except UnknownObjectException:
                raise GithubAPIException(f"Group {namespace} not found.")
        else:
            owner = self.github.get_user()

        new_repo = owner.create_repo(
            name=repo,
            description=description if description else github.GithubObject.NotSet,
        )
        return GithubProject(
            repo=repo,
            namespace=namespace or owner.login,
            service=self,
            github_repo=new_repo,
        )

    def get_pygithub_instance(self, namespace: str, repo: str) -> PyGithubInstance:
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

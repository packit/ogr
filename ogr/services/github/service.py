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

from pathlib import Path
from typing import Type

import github
from github import UnknownObjectException

from ogr.abstract import GitUser
from ogr.exceptions import GithubAPIException
from ogr.factory import use_for_service
from ogr.services.base import BaseGitService
from ogr.services.github.project import GithubProject
from ogr.services.github.user import GithubUser


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
        **_,
    ):
        super().__init__()
        self.token = token

        # Authentication via GitHub app
        self.github_app_id = github_app_id
        self._github_app_private_key = github_app_private_key
        self.github_app_private_key_path = github_app_private_key_path

        self.github = github.Github(login_or_token=self.token)
        self.read_only = read_only

    @property
    def github_app_private_key(self):
        if self._github_app_private_key:
            return self._github_app_private_key

        if self.github_app_private_key_path:
            if not Path(self.github_app_private_key_path).is_file():
                raise GithubAPIException(
                    f"File with the github-app private key "
                    f"({self.github_app_private_key_path}) "
                    f"does not exist."
                )
            return Path(self.github_app_private_key_path).read_text()

        return None

    def __str__(self) -> str:
        token_str = (
            f", token='{self.token[:1]}***{self.token[-1:]}'" if self.token else ""
        )
        github_app_id_str = (
            f", github_app_id='{self.github_app_id[:1]}***{self.github_app_id[-1:]}'"
            if self.github_app_id
            else ""
        )
        github_app_private_key_str = (
            f", github_app_private_key"
            f"='{self._github_app_private_key[:1]}***{self._github_app_private_key[-1:]}'"
            if self._github_app_private_key
            else ""
        )
        github_app_private_key_path_str = (
            f", github_app_private_key_path='{self.github_app_private_key_path}'"
            if self.github_app_private_key_path
            else ""
        )

        readonly_str = ", read_only=True" if self.read_only else ""
        arguments = (
            f"{token_str}"
            f"{github_app_id_str}"
            f"{github_app_private_key_str}"
            f"{github_app_private_key_path_str}"
            f"{readonly_str}"
        )

        if arguments:
            # remove the first '- '
            arguments = arguments[2:]

        return f"GithubService({arguments})"

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, GithubService):
            return False

        return (
            self.token == o.token  # type: ignore
            and self.read_only == o.read_only  # type: ignore
            and self.github_app_id == o.github_app_id  # type: ignore
            and self._github_app_private_key
            == o._github_app_private_key  # type: ignore
            and self.github_app_private_key_path
            == o.github_app_private_key_path  # type: ignore
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
        self, github_repo: github.Repository.Repository
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
        self.token = new_token
        self.github = github.Github(login_or_token=self.token)

    def project_create(self, repo: str, namespace: str = None) -> "GithubProject":
        if namespace:
            try:
                owner = self.github.get_organization(namespace)
            except UnknownObjectException:
                raise GithubAPIException(f"Group {namespace} not found.")
        else:
            owner = self.github.get_user()

        new_repo = owner.create_repo(name=repo)
        return GithubProject(
            repo=repo,
            namespace=namespace or owner.login,
            service=self,
            github_repo=new_repo,
        )

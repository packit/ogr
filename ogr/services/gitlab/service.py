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

import gitlab

from ogr.abstract import GitService, GitUser
from ogr.exceptions import GitlabAPIException
from ogr.factory import use_for_service
from ogr.services.gitlab.project import GitlabProject
from ogr.services.gitlab.user import GitlabUser


@use_for_service("gitlab")
class GitlabService(GitService):
    name = "gitlab"

    def __init__(self, token=None, instance_url=None, ssl_verify=True):
        super().__init__(token=token)
        self.instance_url = instance_url or "https://gitlab.com"
        self.token = token
        self.ssl_verify = ssl_verify
        self._gitlab_instance = None

    @property
    def gitlab_instance(self) -> gitlab.Gitlab:
        if not self._gitlab_instance:
            self._gitlab_instance = gitlab.Gitlab(
                url=self.instance_url,
                private_token=self.token,
                ssl_verify=self.ssl_verify,
            )
            self._gitlab_instance.auth()
        return self._gitlab_instance

    @property
    def user(self) -> GitUser:
        return GitlabUser(service=self)

    def __str__(self) -> str:
        token_str = (
            f", token='{self.token[:1]}***{self.token[-1:]}'" if self.token else ""
        )
        ssl_str = ", ssl_verify=False" if not self.ssl_verify else ""
        str_result = (
            f"GitlabService(instance_url='{self.instance_url}'"
            f"{token_str}"
            f"{ssl_str})"
        )
        return str_result

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, GitlabService):
            return False

        return (
            self.token == o.token  # type: ignore
            and self.instance_url == o.instance_url  # type: ignore
            and self.ssl_verify == o.ssl_verify  # type: ignore
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def get_project(
        self, repo=None, namespace=None, is_fork=False, **kwargs
    ) -> "GitlabProject":
        if is_fork:
            namespace = self.user.get_username()
        return GitlabProject(repo=repo, namespace=namespace, service=self, **kwargs)

    def get_project_from_project_id(self, iid: int) -> "GitlabProject":
        gitlab_repo = self.gitlab_instance.projects.get(iid)
        return GitlabProject(
            repo=gitlab_repo.attributes["path"],
            namespace=gitlab_repo.attributes["namespace"]["full_path"],
            service=self,
            gitlab_repo=gitlab_repo,
        )

    def change_token(self, new_token: str) -> None:
        self.token = new_token
        self._gitlab_instance = None

    def project_create(self, repo: str, namespace: str = None) -> "GitlabProject":
        data = {"name": repo}
        if namespace:
            try:
                group = self.gitlab_instance.groups.get(namespace)
            except gitlab.GitlabGetError:
                raise GitlabAPIException(f"Group {namespace} not found.")
            data["namespace_id"] = group.id
        new_project = self.gitlab_instance.projects.create(data)
        return GitlabProject(
            repo=repo, namespace=namespace, service=self, gitlab_repo=new_project
        )

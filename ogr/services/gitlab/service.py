# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging
from typing import Optional, List

import gitlab

from ogr.abstract import GitUser
from ogr.exceptions import GitlabAPIException, OperationNotSupported
from ogr.factory import use_for_service
from ogr.services.base import BaseGitService, GitProject
from ogr.services.gitlab.project import GitlabProject
from ogr.services.gitlab.user import GitlabUser

logger = logging.getLogger(__name__)


@use_for_service("gitlab")
class GitlabService(BaseGitService):
    name = "gitlab"

    def __init__(self, token=None, instance_url=None, ssl_verify=True, **kwargs):
        super().__init__(token=token)
        self.instance_url = instance_url or "https://gitlab.com"
        self.token = token
        self.ssl_verify = ssl_verify
        self._gitlab_instance = None

        if kwargs:
            logger.warning(f"Ignored keyword arguments: {kwargs}")

    @property
    def gitlab_instance(self) -> gitlab.Gitlab:
        if not self._gitlab_instance:
            self._gitlab_instance = gitlab.Gitlab(
                url=self.instance_url,
                private_token=self.token,
                ssl_verify=self.ssl_verify,
            )
            if self.token:
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

    def project_create(
        self,
        repo: str,
        namespace: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "GitlabProject":
        data = {"name": repo}
        if namespace:
            try:
                group = self.gitlab_instance.groups.get(namespace)
            except gitlab.GitlabGetError as ex:
                raise GitlabAPIException(f"Group {namespace} not found.") from ex
            data["namespace_id"] = group.id

        if description:
            data["description"] = description
        try:
            new_project = self.gitlab_instance.projects.create(data)
        except gitlab.GitlabCreateError as ex:
            raise GitlabAPIException("Project already exists") from ex
        return GitlabProject(
            repo=repo, namespace=namespace, service=self, gitlab_repo=new_project
        )

    def list_projects(
        self,
        namespace: str = None,
        user: str = None,
        search_pattern: str = None,
        language: str = None,
    ) -> List[GitProject]:

        if namespace:
            group = self.gitlab_instance.groups.get(namespace)
            projects = group.projects.list(all=True)
        elif user:
            user_object = self.gitlab_instance.users.list(username=user)[0]
            projects = user_object.projects.list(all=True)
        else:
            raise OperationNotSupported

        gitlab_projects: List[GitProject]

        if language:
            # group.projects.list gives us a GroupProject instance
            # in order to be able to filter by language we need Project instance
            projects_to_convert = [
                self.gitlab_instance.projects.get(item.attributes["id"])
                for item in projects
                if language
                in self.gitlab_instance.projects.get(item.attributes["id"])
                .languages()
                .keys()
            ]
        else:
            projects_to_convert = projects
        gitlab_projects = [
            GitlabProject(
                repo=project.attributes["path"],
                namespace=project.attributes["namespace"]["full_path"],
                gitlab_repo=project,
                service=self,
            )
            for project in projects_to_convert
        ]

        return gitlab_projects

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


from ogr.exceptions import OperationNotSupported
from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BaseGitUser


class GitlabUser(BaseGitUser):
    service: "ogr_gitlab.GitlabService"

    def __init__(self, service: "ogr_gitlab.GitlabService") -> None:
        super().__init__(service=service)

    def __str__(self) -> str:
        return f'GitlabUser(username="{self.get_username()}")'

    @property
    def _gitlab_user(self):
        return self.service.gitlab_instance.user

    def get_username(self) -> str:
        return self._gitlab_user.username

    def get_email(self) -> str:
        return self._gitlab_user.email

    def get_projects(self) -> list["ogr_gitlab.GitlabProject"]:
        raise OperationNotSupported

    def get_forks(self) -> list["ogr_gitlab.GitlabProject"]:
        raise OperationNotSupported

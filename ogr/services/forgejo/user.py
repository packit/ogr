# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


from functools import cached_property

from ogr.services import forgejo
from ogr.services.base import BaseGitUser
from ogr.services.forgejo.project import ForgejoProject


class ForgejoUser(BaseGitUser):
    service: "forgejo.ForgejoService"

    def __init__(self, service: "forgejo.ForgejoService") -> None:
        super().__init__(service=service)
        self._forgejo_user = None

    def __str__(self) -> str:
        return f'ForgejoUser(username="{self.get_username()}")'

    @cached_property
    def forgejo_user(self):
        return self.service.api.user.get_current()

    def get_username(self) -> str:
        return self.forgejo_user.login

    def get_email(self) -> str:
        return self.forgejo_user.email

    def get_projects(self) -> list["ForgejoProject"]:
        repos = self.service.api.user.current_list_repos()
        return [
            ForgejoProject(
                repo=repo.name,
                namespace=repo.owner.login,
                service=self.service,
                forgejo_repo=repo,
            )
            for repo in repos
        ]

    def get_forks(self) -> list["ForgejoProject"]:
        return [project for project in self.get_projects() if project.forgejo_repo.fork]

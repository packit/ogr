# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


from functools import cached_property

from ogr.services import forgejo
from ogr.services.base import BaseGitUser


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

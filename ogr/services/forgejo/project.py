# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


from functools import cached_property
from typing import Optional

from pyforgejo import Repository

from ogr.services import forgejo
from ogr.services.base import BaseGitProject


class ForgejoProject(BaseGitProject):
    service: "forgejo.ForgejoService"

    def __init__(
        self,
        repo: str,
        service: "forgejo.ForgejoService",
        namespace: str,
        forgejo_repo: Optional[Repository] = None,
        **kwargs,
    ):
        super().__init__(repo, service, namespace)
        self._forgejo_repo = forgejo_repo

    @cached_property
    def forgejo_repo(self):
        namespace = self.namespace or self.service.user.get_username()
        return self.service.api.repository.repo_get(
            owner=namespace,
            repo=self.repo,
        )

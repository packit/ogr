# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import List

from ogr.services import pagure as ogr_pagure
from ogr.services.base import BaseGitUser
from ogr.services.pagure.project import PagureProject
from ogr.exceptions import OperationNotSupported


class PagureUser(BaseGitUser):
    service: "ogr_pagure.PagureService"

    def __init__(self, service: "ogr_pagure.PagureService") -> None:
        super().__init__(service=service)

    def __str__(self) -> str:
        return f'PagureUser(username="{self.get_username()}")'

    def get_username(self) -> str:
        request_url = self.service.get_api_url("-", "whoami")

        return_value = self.service.call_api(url=request_url, method="POST", data={})
        return return_value["username"]

    def get_projects(self) -> List["PagureProject"]:
        user_url = self.service.get_api_url("user", self.get_username())
        raw_projects = self.service.call_api(user_url)["repos"]

        return [
            PagureProject(
                repo=project["name"],
                namespace=project["namespace"],
                service=self.service,
            )
            for project in raw_projects
        ]

    def get_forks(self) -> List["PagureProject"]:
        user_url = self.service.get_api_url("user", self.get_username())
        raw_forks = self.service.call_api(user_url)["forks"]

        return [
            PagureProject(
                repo=fork["name"],
                namespace=fork["namespace"],
                service=self.service,
                is_fork=True,
            )
            for fork in raw_forks
        ]

    def get_email(self) -> str:
        # Not supported by Pagure
        raise OperationNotSupported(
            "Pagure does not support retrieving of user's email address"
        )

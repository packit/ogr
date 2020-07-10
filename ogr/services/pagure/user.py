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

from typing import List

from ogr.services import pagure as ogr_pagure
from ogr.services.base import BaseGitUser
from ogr.services.pagure.project import PagureProject


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

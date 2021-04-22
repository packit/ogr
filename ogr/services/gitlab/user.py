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

from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BaseGitUser
from ogr.exceptions import OperationNotSupported


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

    def get_projects(self) -> List["ogr_gitlab.GitlabProject"]:
        raise OperationNotSupported

    def get_forks(self) -> List["ogr_gitlab.GitlabProject"]:
        raise OperationNotSupported

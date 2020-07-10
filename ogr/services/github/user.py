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

from typing import Optional, List

from ogr.services import github as ogr_github
from ogr.services.base import BaseGitUser
from ogr.services.github.project import GithubProject


class GithubUser(BaseGitUser):
    service: "ogr_github.GithubService"

    def __init__(self, service: "ogr_github.GithubService") -> None:
        super().__init__(service=service)

    def __str__(self) -> str:
        return f'GithubUser(username="{self.get_username()}")'

    @property
    def _github_user(self):
        return self.service.github.get_user()

    def get_username(self) -> str:
        return self.service.github.get_user().login

    def get_email(self) -> Optional[str]:
        user_email_property = self.service.github.get_user().email
        if user_email_property:
            return user_email_property

        user_emails = self.service.github.get_user().get_emails()

        if not user_emails:
            return None

        for email_dict in user_emails:
            if email_dict["primary"]:
                return email_dict["email"]

        # Return the first email we received
        return user_emails[0]["email"]

    def get_projects(self) -> List["ogr_github.GithubProject"]:
        raw_repos = self._github_user.get_repos(affiliation="owner")
        return [
            GithubProject(
                repo=repo.name,
                namespace=repo.owner.login,
                github_repo=repo,
                service=self.service,
            )
            for repo in raw_repos
        ]

    def get_forks(self) -> List["ogr_github.GithubProject"]:
        return [project for project in self.get_projects() if project.github_repo.fork]

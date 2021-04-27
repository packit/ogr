# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from collections import namedtuple
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

        # To work around the braking change introduced by pygithub==1.55
        # https://pygithub.readthedocs.io/en/latest/changes.html#version-1-55-april-26-2021
        if isinstance(user_emails[0], dict):
            EmailData = namedtuple("EmailData", user_emails[0].keys())  # type: ignore
        for email in user_emails:
            if "EmailData" in locals():
                email = EmailData(**email)  # type: ignore
            if email.primary:
                return email.email

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

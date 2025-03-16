# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


from functools import cached_property
from typing import Optional

from ogr.abstract import Issue, IssueStatus
from ogr.services import forgejo
from ogr.services.base import BaseGitProject
from ogr.services.forgejo import ForgejoIssue
from ogr.utils import indirect


class ForgejoProject(BaseGitProject):
    service: "forgejo.ForgejoService"

    def __init__(
        self,
        repo: str,
        service: "forgejo.ForgejoService",
        namespace: str,
        **kwargs,
    ):
        super().__init__(repo, service, namespace)
        self._forgejo_repo = None

    @cached_property
    def forgejo_repo(self):
        namespace = self.namespace or self.service.user.get_username()
        return self.service.api.repository.repo_get(
            owner=namespace,
            repo=self.repo,
        )

    @property
    def has_issues(self):
        return self.forgejo_repo.has_issues

    @indirect(ForgejoIssue.get_list)
    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list["Issue"]:
        pass

    @indirect(ForgejoIssue.create)
    def create_issue(
        self,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> Issue:
        pass

    @indirect(ForgejoIssue.get)
    def get_issue(self, issue_id: int) -> "Issue":
        pass

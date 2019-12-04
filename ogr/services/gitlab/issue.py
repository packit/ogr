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

import datetime
from typing import List
import warnings

import gitlab
from gitlab.v4.objects import Issue as _GitlabIssue

from ogr.abstract import IssueComment, IssueStatus, Issue
from ogr.exceptions import GitlabAPIException
from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BaseIssue
from ogr.services.gitlab.comments import GitlabIssueComment


class GitlabIssue(BaseIssue):
    _raw_issue: _GitlabIssue

    @property
    def title(self) -> str:
        return self._raw_issue.title

    @property
    def id(self) -> int:
        return self._raw_issue.iid

    @property
    def status(self) -> IssueStatus:
        return IssueStatus[self._raw_issue.state]

    @property
    def url(self) -> str:
        return self._raw_issue.web_url

    @property
    def description(self) -> str:
        return self._raw_issue.description

    @property
    def author(self) -> str:
        return self._raw_issue.author["username"]

    @property
    def created(self) -> datetime.datetime:
        return self._raw_issue.created_at

    @property
    def labels(self) -> List:
        return self._raw_issue.labels

    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

    @staticmethod
    def create(project: "ogr_gitlab.GitlabProject", title: str, body: str) -> "Issue":
        issue = project.gitlab_repo.issues.create({"title": title, "description": body})
        return GitlabIssue(issue, project)

    @staticmethod
    def get(project: "ogr_gitlab.GitlabProject", id: int) -> "Issue":
        try:
            return GitlabIssue(project.gitlab_repo.issues.get(id), project)
        except gitlab.exceptions.GitlabGetError as ex:
            raise GitlabAPIException(f"Issue {id} was not found. ", ex)

    @staticmethod
    def get_list(
        project: "ogr_gitlab.GitlabProject", status: IssueStatus = IssueStatus.open
    ) -> List["Issue"]:
        if status == IssueStatus.open:
            warnings.warn(
                "Using deprecated constant, that will be removed in 0.14.0"
                "(or 1.0.0 if it comes sooner). Please use opened.",
                DeprecationWarning,
            )
            status = IssueStatus.opened

        issues = project.gitlab_repo.issues.list(
            state=status.name, order_by="updated_at", sort="desc"
        )
        return [GitlabIssue(issue, project) for issue in issues]

    def _get_all_comments(self) -> List[IssueComment]:
        return [
            GitlabIssueComment(parent=self, raw_comment=raw_comment)
            for raw_comment in self._raw_issue.notes.list(sort="asc")
        ]

    def comment(self, body: str) -> IssueComment:
        comment = self._raw_issue.notes.create({"body": body})
        return GitlabIssueComment(parent=self, raw_comment=comment)

    def close(self) -> "Issue":
        self._raw_issue.state_event = "close"
        self._raw_issue.save()
        return self

    def add_label(self, *labels: str) -> None:
        for label in labels:
            self._raw_issue.labels.append(label)
        self._raw_issue.save()

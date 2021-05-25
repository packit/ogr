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
from typing import List, Optional, Dict, Union

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

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_issue.title = new_title
        self._raw_issue.save()

    @property
    def id(self) -> int:
        return self._raw_issue.iid

    @property
    def private(self) -> bool:
        return self._raw_issue.confidential

    @property
    def status(self) -> IssueStatus:
        return (
            IssueStatus.open
            if self._raw_issue.state == "opened"
            else IssueStatus[self._raw_issue.state]
        )

    @property
    def url(self) -> str:
        return self._raw_issue.web_url

    @property
    def assignees(self) -> list:
        try:
            return self._raw_issue.assignees
        except AttributeError:
            return None  # if issue has no assignees, the attribute is not present

    @property
    def description(self) -> str:
        return self._raw_issue.description

    @description.setter
    def description(self, new_description: str) -> None:
        self._raw_issue.description = new_description
        self._raw_issue.save()

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
    def create(
        project: "ogr_gitlab.GitlabProject",
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> "Issue":
        assignee_ids = []
        for user in assignees or []:
            users_list = project.service.gitlab_instance.users.list(username=user)

            if not users_list:
                raise GitlabAPIException(f"Unable to find '{user}' username")

            assignee_ids.append(str(users_list[0].id))

        data = {"title": title, "description": body}
        if labels:
            data["labels"] = ",".join(labels)
        if assignees:
            data["assignee_ids"] = ",".join(assignee_ids)

        issue = project.gitlab_repo.issues.create(data, confidential=private)
        return GitlabIssue(issue, project)

    @staticmethod
    def get(project: "ogr_gitlab.GitlabProject", issue_id: int) -> "Issue":
        try:
            return GitlabIssue(project.gitlab_repo.issues.get(issue_id), project)
        except gitlab.exceptions.GitlabGetError as ex:
            raise GitlabAPIException(f"Issue {issue_id} was not found. ", ex)

    @staticmethod
    def get_list(
        project: "ogr_gitlab.GitlabProject",
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List["Issue"]:
        # Gitlab API has status 'opened', not 'open'
        parameters: Dict[str, Union[str, List[str], bool]] = {
            "state": status.name if status != IssueStatus.open else "opened",
            "order_by": "updated_at",
            "sort": "desc",
            "all": True,
        }
        if author:
            parameters["author_username"] = author
        if assignee:
            parameters["assignee_username"] = assignee
        if labels:
            parameters["labels"] = labels

        issues = project.gitlab_repo.issues.list(**parameters)
        return [GitlabIssue(issue, project) for issue in issues]

    def _get_all_comments(self) -> List[IssueComment]:
        return [
            GitlabIssueComment(parent=self, raw_comment=raw_comment)
            for raw_comment in self._raw_issue.notes.list(sort="asc", all=True)
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

    def add_assignee(self, *assignees: str) -> None:
        assignee_ids = self._raw_issue.__dict__.get("assignee_ids") or []
        for assignee in assignees:
            users = self.project.service.gitlab_instance.users.list(  # type: ignore
                username=assignee
            )
            if not users:
                raise GitlabAPIException(f"Unable to find '{assignee}' username")
            uid = str(users[0].id)
            if uid not in assignee_ids:
                assignee_ids.append(str(users[0].id))

        self._raw_issue.assignee_ids = assignee_ids
        self._raw_issue.save()

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import List, Optional, Dict, Union

import gitlab
from gitlab.v4.objects import Issue as _GitlabIssue

from ogr.abstract import IssueComment, IssueStatus, Issue
from ogr.exceptions import GitlabAPIException, IssueTrackerDisabled
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
    def assignees(self) -> Optional[List[str]]:
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
        if not project.has_issues:
            raise IssueTrackerDisabled()

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
        if not project.has_issues:
            raise IssueTrackerDisabled()

        try:
            return GitlabIssue(project.gitlab_repo.issues.get(issue_id), project)
        except gitlab.exceptions.GitlabGetError as ex:
            raise GitlabAPIException(f"Issue {issue_id} was not found. ") from ex

    @staticmethod
    def get_list(
        project: "ogr_gitlab.GitlabProject",
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List["Issue"]:
        if not project.has_issues:
            raise IssueTrackerDisabled()

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

    def get_comment(self, comment_id: int) -> IssueComment:
        return GitlabIssueComment(self._raw_issue.notes.get(comment_id))

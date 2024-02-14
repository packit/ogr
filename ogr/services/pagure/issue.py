# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import Any, Optional, Union, cast

from ogr.abstract import Issue, IssueComment, IssueLabel, IssueStatus
from ogr.exceptions import (
    IssueTrackerDisabled,
    OperationNotSupported,
    PagureAPIException,
)
from ogr.services import pagure as ogr_pagure
from ogr.services.base import BaseIssue
from ogr.services.pagure.comments import PagureIssueComment
from ogr.services.pagure.label import PagureIssueLabel


class PagureIssue(BaseIssue):
    project: "ogr_pagure.PagureProject"

    def __init__(self, raw_issue, project):
        super().__init__(raw_issue, project)
        self.__dirty = False

    def __update(self):
        if self.__dirty:
            self._raw_issue = self.project._call_project_api("issue", str(self.id))
            self.__dirty = False

    @property
    def title(self) -> str:
        self.__update()
        return self._raw_issue["title"]

    @title.setter
    def title(self, new_title: str) -> None:
        self.__update_info(title=new_title)

    @property
    def private(self) -> bool:
        self.__update()
        return self._raw_issue["private"]

    @property
    def id(self) -> int:
        return self._raw_issue["id"]

    @property
    def status(self) -> IssueStatus:
        self.__update()
        return IssueStatus[self._raw_issue["status"].lower()]

    @property
    def url(self) -> str:
        return self.project._get_project_url(
            "issue",
            str(self.id),
            add_api_endpoint_part=False,
        )

    @property
    def assignee(self) -> str:
        self.__update()
        try:
            return self._raw_issue["assignee"]["name"]
        except Exception:
            return None

    @property
    def description(self) -> str:
        self.__update()
        return self._raw_issue["content"]

    @description.setter
    def description(self, new_description: str) -> None:
        self.__update_info(description=new_description)

    @property
    def author(self) -> str:
        return self._raw_issue["user"]["name"]

    @property
    def created(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(int(self._raw_issue["date_created"]))

    @property
    def labels(self) -> list[IssueLabel]:
        return [PagureIssueLabel(label, self) for label in self._raw_issue["tags"]]

    def __str__(self) -> str:
        return "Pagure" + super().__str__()

    def __update_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> None:
        try:
            data = {
                "title": title if title is not None else self.title,
                "issue_content": (
                    description if description is not None else self.description
                ),
            }

            updated_issue = self.project._call_project_api(
                "issue",
                str(self.id),
                method="POST",
                data=data,
            )
            self._raw_issue = updated_issue["issue"]
        except Exception as ex:
            raise PagureAPIException(
                "there was an error while updating the issue",
            ) from ex

    @staticmethod
    def create(
        project: "ogr_pagure.PagureProject",
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> "Issue":
        if not project.has_issues:
            raise IssueTrackerDisabled()

        payload = {"title": title, "issue_content": body}
        if labels is not None:
            payload["tag"] = ",".join(labels)
        if private:
            payload["private"] = "true"
        if assignees and len(assignees) > 1:
            raise OperationNotSupported("Pagure does not support multiple assignees")

        if assignees:
            payload["assignee"] = assignees[0]

        new_issue = project._call_project_api("new_issue", data=payload, method="POST")[
            "issue"
        ]
        return PagureIssue(new_issue, project)

    @staticmethod
    def get(project: "ogr_pagure.PagureProject", issue_id: int) -> "Issue":
        if not project.has_issues:
            raise IssueTrackerDisabled()

        raw_issue = project._call_project_api("issue", str(issue_id))
        return PagureIssue(raw_issue, project)

    @staticmethod
    def get_list(
        project: "ogr_pagure.PagureProject",
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list["Issue"]:
        if not project.has_issues:
            raise IssueTrackerDisabled()

        payload: dict[str, Union[str, list[str], int]] = {
            "status": status.name.capitalize(),
            "page": 1,
            "per_page": 100,
        }
        if author:
            payload["author"] = author
        if assignee:
            payload["assignee"] = assignee
        if labels:
            payload["tags"] = labels

        raw_issues: list[Any] = []

        while True:
            issues_info = project._call_project_api("issues", params=payload)
            raw_issues += issues_info["issues"]
            if not issues_info["pagination"]["next"]:
                break
            payload["page"] = cast(int, payload["page"]) + 1

        return [PagureIssue(issue_dict, project) for issue_dict in raw_issues]

    def _get_all_comments(self) -> list[IssueComment]:
        self.__update()
        raw_comments = self._raw_issue["comments"]
        return [
            PagureIssueComment(parent=self, raw_comment=raw_comment)
            for raw_comment in raw_comments
        ]

    def comment(self, body: str) -> IssueComment:
        payload = {"comment": body}
        self.project._call_project_api(
            "issue",
            str(self.id),
            "comment",
            data=payload,
            method="POST",
        )
        self.__dirty = True
        return PagureIssueComment(parent=self, body=body, author=self.project._user)

    def close(self) -> "PagureIssue":
        payload = {"status": "Closed"}
        self.project._call_project_api(
            "issue",
            str(self.id),
            "status",
            data=payload,
            method="POST",
        )
        self.__dirty = True
        return self

    def add_assignee(self, *assignees: str) -> None:
        if len(assignees) > 1:
            raise OperationNotSupported("Pagure does not support multiple assignees")
        payload = {"assignee": assignees[0]}
        self.project._call_project_api(
            "issue",
            str(self.id),
            "assign",
            data=payload,
            method="POST",
        )

    def get_comment(self, comment_id: int) -> IssueComment:
        return PagureIssueComment(
            self.project._call_project_api(
                "issue",
                str(self.id),
                "comment",
                str(comment_id),
                method="GET",
            ),
        )

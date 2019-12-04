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

from ogr.abstract import IssueComment, IssueStatus, Issue
from ogr.services import pagure as ogr_pagure
from ogr.services.base import BaseIssue
from ogr.services.pagure.comments import PagureIssueComment


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

    @property
    def id(self) -> int:
        return self._raw_issue["id"]

    @property
    def status(self) -> IssueStatus:
        self.__update()
        state = self._raw_issue["status"].lower()
        return IssueStatus[state] if state != "open" else IssueStatus.opened

    @property
    def url(self) -> str:
        return self.project._get_project_url(
            "issue", str(self.id), add_api_endpoint_part=False
        )

    @property
    def description(self) -> str:
        self.__update()
        return self._raw_issue["content"]

    @property
    def author(self) -> str:
        return self._raw_issue["user"]["name"]

    @property
    def created(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(int(self._raw_issue["date_created"]))

    def __str__(self) -> str:
        return "Pagure" + super().__str__()

    @staticmethod
    def create(project: "ogr_pagure.PagureProject", title: str, body: str) -> "Issue":
        payload = {"title": title, "issue_content": body}
        new_issue = project._call_project_api("new_issue", data=payload, method="POST")[
            "issue"
        ]
        return PagureIssue(new_issue, project)

    @staticmethod
    def get(project: "ogr_pagure.PagureProject", id: int) -> "Issue":
        raw_issue = project._call_project_api("issue", str(id))
        return PagureIssue(raw_issue, project)

    @staticmethod
    def get_list(
        project: "ogr_pagure.PagureProject", status: IssueStatus = IssueStatus.opened
    ) -> List["Issue"]:
        if status == IssueStatus.open:
            warnings.warn(
                "Using deprecated constant, that will be removed in 0.14.0"
                "(or 1.0.0 if it comes sooner). Please use opened.",
                DeprecationWarning,
            )
            status = IssueStatus.opened

        state = status.name.capitalize() if status != IssueStatus.opened else "OPEN"
        payload = {"status": state}

        raw_issues = project._call_project_api("issues", params=payload)["issues"]
        return [PagureIssue(issue_dict, project) for issue_dict in raw_issues]

    def _get_all_comments(self) -> List[IssueComment]:
        self.__update()
        raw_comments = self._raw_issue["comments"]
        return [
            PagureIssueComment(parent=self, raw_comment=raw_comment)
            for raw_comment in raw_comments
        ]

    def comment(self, body: str) -> IssueComment:
        payload = {"comment": body}
        self.project._call_project_api(
            "issue", str(self.id), "comment", data=payload, method="POST"
        )
        self.__dirty = True
        return PagureIssueComment(parent=self, body=body, author=self.project._user)

    def close(self) -> "PagureIssue":
        payload = {"status": "Closed"}
        self.project._call_project_api(
            "issue", str(self.id), "status", data=payload, method="POST"
        )
        self.__dirty = True
        return self

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
from typing import List, Optional, Dict, Union, Any, cast

from ogr.abstract import IssueComment, IssueStatus, Issue
from ogr.exceptions import PagureAPIException
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
            "issue", str(self.id), add_api_endpoint_part=False
        )

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
    def labels(self) -> List[str]:
        return self._raw_issue["tags"]

    def __str__(self) -> str:
        return "Pagure" + super().__str__()

    def __update_info(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        try:
            data = {
                "title": title if title is not None else self.title,
                "issue_content": description
                if description is not None
                else self.description,
            }

            updated_issue = self.project._call_project_api(
                "issue", str(self.id), method="POST", data=data
            )
            self._raw_issue = updated_issue["issue"]
        except Exception as ex:
            raise PagureAPIException("there was an error while updating the issue", ex)

    @staticmethod
    def create(
        project: "ogr_pagure.PagureProject",
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[List[str]] = None,
    ) -> "Issue":
        payload = {"title": title, "issue_content": body}
        if labels is not None:
            payload["tag"] = ",".join(labels)
        if private:
            payload["private"] = "true"
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
        project: "ogr_pagure.PagureProject",
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List["Issue"]:
        payload: Dict[str, Union[str, List[str], int]] = {
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

        raw_issues: List[Any] = []

        while True:
            issues_info = project._call_project_api("issues", params=payload)
            raw_issues += issues_info["issues"]
            if not issues_info["pagination"]["next"]:
                break
            payload["page"] = cast(int, payload["page"]) + 1

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

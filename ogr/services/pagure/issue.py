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

from ogr.abstract import IssueComment, IssueStatus
from ogr.services import pagure as ogr_pagure
from ogr.services.base import BaseIssue
from ogr.services.pagure.comments import PagureIssueComment


class PagureIssue(BaseIssue):
    project: "ogr_pagure.PagureProject"

    @property
    def title(self) -> str:
        return self._raw_issue["title"]

    @property
    def id(self) -> int:
        return self._raw_issue["id"]

    @property
    def status(self) -> IssueStatus:
        return IssueStatus[self._raw_issue["status"].lower()]

    @property
    def url(self) -> str:
        return self.project._get_project_url(
            "issue", str(self.id), add_api_endpoint_part=False
        )

    @property
    def description(self) -> str:
        return self._raw_issue["content"]

    @property
    def author(self) -> str:
        return self._raw_issue["user"]["name"]

    @property
    def created(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(int(self._raw_issue["date_created"]))

    def __str__(self) -> str:
        return "Pagure" + super().__str__()

    def _get_all_comments(self) -> List[IssueComment]:
        raw_comments = self._raw_issue["comments"]
        return [PagureIssueComment(raw_comment) for raw_comment in raw_comments]

    def comment(self, body: str) -> IssueComment:
        payload = {"comment": body}
        self.project._call_project_api(
            "issue", str(self.id), "comment", data=payload, method="POST"
        )
        return PagureIssueComment(comment=body, author=self.project._user)

    def close(self) -> "PagureIssue":
        payload = {"status": "Closed"}
        self.project._call_project_api(
            "issue", str(self.id), "status", data=payload, method="POST"
        )
        # TODO: update self
        return self

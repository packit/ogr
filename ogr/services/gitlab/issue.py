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

from typing import List

from gitlab.v4.objects import GitlabIssue as _GitlabIssue

from ogr.abstract import IssueComment, IssueStatus
from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BaseIssue
from ogr.services.gitlab.comments import GitlabIssueComment


class GitlabIssue(BaseIssue):
    def __init__(
        self, raw_issue: _GitlabIssue, project: "ogr_gitlab.GitlabProject"
    ) -> None:
        super().__init__(
            title=raw_issue.title,
            id=raw_issue.iid,
            status=IssueStatus.open
            if raw_issue.state == "opened"
            else IssueStatus[raw_issue.state],
            url=raw_issue.web_url,
            description=raw_issue.description,
            author=raw_issue.author["username"],
            created=raw_issue.created_at,
        )
        self.project = project
        self._raw_issue = raw_issue

    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

    def _get_all_comments(self) -> List[IssueComment]:
        return [
            GitlabIssueComment(raw_comment)
            for raw_comment in self._raw_issue.notes.list(sort="asc")
        ]

    def issue_comment(self, body: str) -> IssueComment:
        comment = self._raw_issue.notes.create({"body": body})
        return GitlabIssueComment(comment)

    def close(self) -> "GitlabIssue":
        self._raw_issue.state_event = "close"
        self._raw_issue.save()
        # TODO: update self
        return self

    def get_labels(self) -> List:
        return self._raw_issue.labels

    def add_labels(self, labels: List[str]) -> None:
        for label in labels:
            self._raw_issue.labels.append(label)
        self._raw_issue.save()

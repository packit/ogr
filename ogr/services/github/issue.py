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

from github.Issue import Issue as _GithubIssue

from ogr.abstract import IssueComment, IssueStatus
from ogr.exceptions import GithubAPIException
from ogr.services import github as ogr_github
from ogr.services.base import BaseIssue
from ogr.services.github.comments import GithubIssueComment


class GithubIssue(BaseIssue):
    def __init__(
        self, raw_issue: _GithubIssue, project: "ogr_github.GithubProject"
    ) -> None:
        if raw_issue.pull_request:
            raise GithubAPIException(
                f"Requested issue #{raw_issue.number} is a pull request"
            )

        super().__init__(
            title=raw_issue.title,
            id=raw_issue.number,
            status=IssueStatus[raw_issue.state],
            url=raw_issue.html_url,
            description=raw_issue.body,
            author=raw_issue.user.login,
            created=raw_issue.created_at,
        )
        self.project = project
        self._raw_issue = raw_issue

    def __str__(self) -> str:
        return "Github" + super().__str__()

    def _get_all_comments(self) -> List[IssueComment]:
        return [
            GithubIssueComment(raw_comment)
            for raw_comment in self._raw_issue.get_comments()
        ]

    def issue_comment(self, body: str) -> IssueComment:
        comment = self._raw_issue.create_comment(body)
        return GithubIssueComment(comment)

    def close(self) -> "GithubIssue":
        self._raw_issue.edit(state="closed")
        return self

    def get_labels(self) -> List:
        return list(self._raw_issue.get_labels())

    def add_labels(self, labels: List[str]) -> None:
        for label in labels:
            self._raw_issue.add_to_labels(label)

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
from typing import List, Optional

from gitlab.v4.objects import MergeRequest as _GitlabMergeRequest

from ogr.abstract import PullRequest, PRComment, PRStatus
from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BasePullRequest
from ogr.services.gitlab.comments import GitlabPRComment


class GitlabPullRequest(BasePullRequest):
    _raw_pr: _GitlabMergeRequest
    project: "ogr_gitlab.GitlabProject"

    @property
    def title(self) -> str:
        return self._raw_pr.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_pr.title = new_title
        self._raw_pr.save()

    @property
    def id(self) -> int:
        return self._raw_pr.iid

    @property
    def status(self) -> PRStatus:
        return (
            PRStatus.open
            if self._raw_pr.state == "opened"
            else PRStatus[self._raw_pr.state]
        )

    @property
    def url(self) -> str:
        return self._raw_pr.web_url

    @property
    def description(self) -> str:
        return self._raw_pr.description

    @description.setter
    def description(self, new_description: str) -> None:
        self._raw_pr.description = new_description
        self._raw_pr.save()

    @property
    def author(self) -> str:
        return self._raw_pr.author["username"]

    @property
    def source_branch(self) -> str:
        return self._raw_pr.source_branch

    @property
    def target_branch(self) -> str:
        return self._raw_pr.target_branch

    @property
    def created(self) -> datetime.datetime:
        return self._raw_pr.created_at

    @property
    def labels(self) -> List[str]:
        return self._raw_pr.labels

    @property
    def diff_url(self) -> str:
        return f"{self._raw_pr.web_url}/diffs"

    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

    @staticmethod
    def create(
        project: "ogr_gitlab.GitlabProject",
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        mr = project.gitlab_repo.mergerequests.create(
            {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": body,
            }
        )
        return GitlabPullRequest(mr, project)

    @staticmethod
    def get(project: "ogr_gitlab.GitlabProject", id: int) -> "PullRequest":
        mr = project.gitlab_repo.mergerequests.get(id)
        return GitlabPullRequest(mr, project)

    @staticmethod
    def get_list(
        project: "ogr_gitlab.GitlabProject", status: PRStatus = PRStatus.open
    ) -> List["PullRequest"]:
        # Gitlab API has status 'opened', not 'open'
        mrs = project.gitlab_repo.mergerequests.list(
            state=status.name if status != PRStatus.open else "opened",
            order_by="updated_at",
            sort="desc",
        )
        return [GitlabPullRequest(mr, project) for mr in mrs]

    def update_info(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> "PullRequest":
        if title:
            self._raw_pr.title = title
        if description:
            self._raw_pr.description = description

        self._raw_pr.save()
        return self

    def _get_all_comments(self) -> List[PRComment]:
        return [
            GitlabPRComment(parent=self, raw_comment=raw_comment)
            for raw_comment in self._raw_pr.notes.list(sort="asc")
        ]

    def get_all_commits(self) -> List[str]:
        return [commit.id for commit in self._raw_pr.commits()]

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
        comment = self._raw_pr.notes.create({"body": body})
        return GitlabPRComment(parent=self, raw_comment=comment)

    def close(self) -> "PullRequest":
        self._raw_pr.state_event = "close"
        self._raw_pr.save()
        return self

    def merge(self) -> "PullRequest":
        self._raw_pr.merge()
        return self

    def add_label(self, *labels: str) -> None:
        self._raw_pr.labels += labels
        self._raw_pr.save()

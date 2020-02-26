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
import logging
from typing import Optional, List

from github import UnknownObjectException
from github.Label import Label as GithubLabel
from github.PullRequest import PullRequest as _GithubPullRequest

from ogr.abstract import PRComment, PRStatus, PullRequest
from ogr.exceptions import GithubAPIException
from ogr.services import github as ogr_github
from ogr.services.base import BasePullRequest
from ogr.services.github.comments import GithubPRComment

logger = logging.getLogger(__name__)


class GithubPullRequest(BasePullRequest):
    _raw_pr: _GithubPullRequest
    project: "ogr_github.GithubProject"

    @property
    def title(self) -> str:
        return self._raw_pr.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_pr.edit(title=new_title)

    @property
    def id(self) -> int:
        return self._raw_pr.number

    @property
    def status(self) -> PRStatus:
        return (
            PRStatus.merged
            if self._raw_pr.is_merged()
            else PRStatus[self._raw_pr.state]
        )

    @property
    def url(self) -> str:
        return self._raw_pr.html_url

    @property
    def description(self) -> str:
        return self._raw_pr.body

    @description.setter
    def description(self, new_description: str) -> None:
        self._raw_pr.edit(body=new_description)

    @property
    def author(self) -> str:
        return self._raw_pr.user.login

    @property
    def source_branch(self) -> str:
        return self._raw_pr.head.ref

    @property
    def target_branch(self) -> str:
        return self._raw_pr.base.ref

    @property
    def created(self) -> datetime.datetime:
        return self._raw_pr.created_at

    @property
    def labels(self) -> List[GithubLabel]:
        return list(self._raw_pr.get_labels())

    @property
    def diff_url(self) -> str:
        return f"{self._raw_pr.html_url}/files"

    def __str__(self) -> str:
        return "Github" + super().__str__()

    @staticmethod
    def create(
        project: "ogr_github.GithubProject",
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        github_repo = project.github_repo

        if project.is_fork and fork_username:
            logger.warning(
                f"{project.full_repo_name} is fork, ignoring fork_username arg"
            )

        if project.is_fork:
            source_branch = f"{project.namespace}:{source_branch}"
            github_repo = project.parent.github_repo
        elif fork_username:
            source_branch = f"{fork_username}:{source_branch}"

        created_pr = github_repo.create_pull(
            title=title, body=body, base=target_branch, head=source_branch
        )
        logger.info(f"PR {created_pr.id} created: {target_branch}<-{source_branch}")
        return GithubPullRequest(created_pr, project)

    @staticmethod
    def get(project: "ogr_github.GithubProject", id: int) -> "PullRequest":
        pr = project.github_repo.get_pull(number=id)
        return GithubPullRequest(pr, project)

    @staticmethod
    def get_list(
        project: "ogr_github.GithubProject", status: PRStatus = PRStatus.open
    ) -> List["PullRequest"]:
        prs = project.github_repo.get_pulls(
            # Github API has no status 'merged', just 'closed'/'opened'/'all'
            state=status.name if status != PRStatus.merged else "closed",
            sort="updated",
            direction="desc",
        )

        if status == PRStatus.merged:
            prs = list(prs)  # Github PaginatedList into list()
            for pr in prs:
                if not pr.is_merged():  # parse merged PRs
                    prs.remove(pr)
        try:
            return [GithubPullRequest(pr, project) for pr in prs]
        except UnknownObjectException:
            return []

    def update_info(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> "PullRequest":
        try:
            self._raw_pr.edit(title=title, body=description)
            logger.info(f"PR updated: {self._raw_pr.url}")
            return self
        except Exception as ex:
            raise GithubAPIException("there was an error while updating the PR", ex)

    def _get_all_comments(self) -> List[PRComment]:
        return [
            GithubPRComment(parent=self, raw_comment=raw_comment)
            for raw_comment in self._raw_pr.get_issue_comments()
        ]

    def get_all_commits(self) -> List[str]:
        return [commit.sha for commit in self._raw_pr.get_commits()]

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
        if not any([commit, filename, row]):
            comment = self._raw_pr.create_issue_comment(body)
        else:
            github_commit = self.project.github_repo.get_commit(commit)
            comment = self._raw_pr.create_comment(body, github_commit, filename, row)
        return GithubPRComment(parent=self, raw_comment=comment)

    def close(self) -> "PullRequest":
        self._raw_pr.edit(state=PRStatus.closed.name)
        return self

    def merge(self) -> "PullRequest":
        self._raw_pr.merge()
        return self

    def add_label(self, *labels: str) -> None:
        for label in labels:
            self._raw_pr.add_to_labels(label)

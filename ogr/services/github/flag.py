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
from typing import List, Union

from github import UnknownObjectException

from ogr.abstract import CommitFlag, CommitStatus
from ogr.services import github as ogr_github
from ogr.services.base import BaseCommitFlag


class GithubCommitFlag(BaseCommitFlag):
    _states = {
        "pending": CommitStatus.pending,
        "success": CommitStatus.success,
        "failure": CommitStatus.failure,
        "error": CommitStatus.error,
    }

    def __str__(self) -> str:
        return "Github" + super().__str__()

    def _from_raw_commit_flag(self):
        self.state = self._state_from_str(self._raw_commit_flag.state)
        self.context = self._raw_commit_flag.context
        self.comment = self._raw_commit_flag.description
        self.url = self._raw_commit_flag.target_url
        self.uid = self._raw_commit_flag.id

    @staticmethod
    def get(project: "ogr_github.GithubProject", commit: str) -> List["CommitFlag"]:
        statuses = project.github_repo.get_commit(commit).get_statuses()

        try:
            return [
                GithubCommitFlag(
                    raw_commit_flag=raw_status, project=project, commit=commit
                )
                for raw_status in statuses
            ]
        except UnknownObjectException:
            return []

    @staticmethod
    def set(
        project: "ogr_github.GithubProject",
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "CommitFlag":
        state = GithubCommitFlag._validate_state(state)

        github_commit = project.github_repo.get_commit(commit)
        if trim:
            description = description[:140]
        status = github_commit.create_status(
            state.name, target_url, description, context
        )
        return GithubCommitFlag(project=project, raw_commit_flag=status, commit=commit)

    @property
    def created(self) -> datetime.datetime:
        return self._raw_commit_flag.created_at

    @property
    def edited(self) -> datetime.datetime:
        return self._raw_commit_flag.updated_at

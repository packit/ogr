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

from github import UnknownObjectException

from ogr.abstract import CommitFlag
from ogr.services import github as ogr_github


class GithubCommitFlag(CommitFlag):
    def __str__(self) -> str:
        return "Github" + super().__str__()

    def _from_raw_commit_flag(self):
        self.state = self._raw_commit_flag.state
        self.context = self._raw_commit_flag.context
        self.comment = self._raw_commit_flag.description

    @staticmethod
    def get(project: "ogr_github.GithubProject", commit: str) -> List["CommitFlag"]:
        statuses = project.github_repo.get_commit(commit).get_statuses()

        try:
            return [
                GithubCommitFlag(raw_commit_flag=raw_status, project=project)
                for raw_status in statuses
            ]
        except UnknownObjectException:
            return []

    @staticmethod
    def set(
        project: "ogr_github.GithubProject",
        commit: str,
        state: str,
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "CommitFlag":
        github_commit = project.github_repo.get_commit(commit)
        if trim:
            description = description[:140]
        status = github_commit.create_status(state, target_url, description, context)
        return GithubCommitFlag(project=project, raw_commit_flag=status, commit=commit)

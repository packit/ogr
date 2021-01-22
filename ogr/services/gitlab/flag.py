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

import logging
import datetime
from typing import List, Union

import gitlab

from ogr.abstract import CommitFlag, CommitStatus
from ogr.exceptions import GitlabAPIException, OperationNotSupported
from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BaseCommitFlag

logger = logging.getLogger(__name__)


class GitlabCommitFlag(BaseCommitFlag):
    _states = {
        "pending": CommitStatus.pending,
        "success": CommitStatus.success,
        "failed": CommitStatus.failure,
        "canceled": CommitStatus.canceled,
        "running": CommitStatus.running,
    }

    @staticmethod
    def _state_from_enum(state: CommitStatus) -> str:
        return "failed" if state == CommitStatus.failure else state.name

    def __str__(self) -> str:
        return (
            f"GitlabCommitFlag("
            f"commit='{self.commit}', "
            f"state='{self.state.name}', "
            f"context='{self.context}', "
            f"uid='{self.uid}', "
            f"comment='{self.comment}', "
            f"url='{self.url}', "
            f"created='{self.created}')"
        )

    def _from_raw_commit_flag(self):
        self.commit = self._raw_commit_flag.sha
        self.state = self._state_from_str(self._raw_commit_flag.status)
        self.context = self._raw_commit_flag.name
        self.comment = self._raw_commit_flag.description
        self.uid = self._raw_commit_flag.id
        self.url = self._raw_commit_flag.target_url

    @staticmethod
    def get(project: "ogr_gitlab.GitlabProject", commit: str) -> List["CommitFlag"]:
        try:
            commit_object = project.gitlab_repo.commits.get(commit)
        except gitlab.exceptions.GitlabGetError:
            logger.error(f"Commit {commit} was not found.")
            raise GitlabAPIException(f"Commit {commit} was not found.")

        raw_statuses = commit_object.statuses.list(all=True)
        return [
            GitlabCommitFlag(raw_commit_flag=raw_status, project=project)
            for raw_status in raw_statuses
        ]

    @staticmethod
    def set(
        project: "ogr_gitlab.GitlabProject",
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "CommitFlag":
        state = GitlabCommitFlag._validate_state(state)

        if trim:
            description = description[:140]

        try:
            commit_object = project.gitlab_repo.commits.get(commit)
        except gitlab.exceptions.GitlabGetError:
            logger.error(f"Commit {commit} was not found.")
            raise GitlabAPIException(f"Commit {commit} was not found.")

        data_dict = {
            "state": GitlabCommitFlag._state_from_enum(state),
            "target_url": target_url,
            "context": context,
            "description": description,
        }
        raw_status = commit_object.statuses.create(data_dict)
        return GitlabCommitFlag(raw_commit_flag=raw_status, project=project)

    @property
    def created(self) -> datetime.datetime:
        return datetime.datetime.strptime(
            self._raw_commit_flag.created_at, "%Y-%m-%dT%H:%M:%S.%fZ"
        )

    @property
    def edited(self) -> datetime.datetime:
        raise OperationNotSupported(
            "GitLab doesn't support edited on commit flags, for more info "
            "see https://github.com/packit/ogr/issues/413#issuecomment-729623702"
        )

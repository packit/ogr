# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import List

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
        state: CommitStatus,
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

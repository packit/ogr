# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import logging
from collections.abc import Iterable
from typing import ClassVar, Union

import pyforgejo

from ogr.abstract import CommitStatus
from ogr.exceptions import ForgejoAPIException
from ogr.services import forgejo as ogr_forgejo
from ogr.services.base import BaseCommitFlag

from .utils import paginate

logger = logging.getLogger(__name__)


class ForgejoCommitFlag(BaseCommitFlag):
    _states: ClassVar[dict[str, CommitStatus]] = {
        "pending": CommitStatus.pending,
        "success": CommitStatus.success,
        "failed": CommitStatus.failure,
        "canceled": CommitStatus.error,
        "warning": CommitStatus.warning,
    }

    @staticmethod
    def _state_from_enum(state: CommitStatus) -> str:
        return "failed" if state == CommitStatus.failure else state.name

    def __str__(self) -> str:
        return (
            f"ForgejoCommitFlag("
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
        self.state = self._state_from_str(self._raw_commit_flag.state)
        self.context = self._raw_commit_flag.context
        self.comment = self._raw_commit_flag.description
        self.uid = self._raw_commit_flag.id
        self.url = self._raw_commit_flag.target_url

    @staticmethod
    def get(
        project: "ogr_forgejo.ForgejoProject",
        commit: str,
    ) -> Iterable["ForgejoCommitFlag"]:

        try:
            statuses = project.get_commit_statuses(commit)
        except pyforgejo.NotFoundError as ex:  # 404 error
            logger.error(f"Commit {commit} was not found.")
            raise ForgejoAPIException(f"Commit {commit} was not found.") from ex

        return (
            ForgejoCommitFlag(
                raw_commit_flag=status,
                project=project,
                commit=commit,
            )
            for status in paginate(statuses)
        )

    @staticmethod
    def set(
        project: "ogr_forgejo.ForgejoProject",
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "ForgejoCommitFlag":

        if isinstance(state, str):
            state = super(ForgejoCommitFlag, ForgejoCommitFlag)._state_from_str(state)

        state = ForgejoCommitFlag._validate_state(state)

        if trim:
            description = description[:140]

        owner = project.forgejo_repo.owner.full_name
        forgejo_repo = project.forgejo_repo

        try:
            status = project.api.repo_create_status(
                owner=owner,
                repo=forgejo_repo.name,
                sha=commit,
                context=context,
                description=description,
                state=state.name,
                target_url=target_url,
                request_options=None,
            )

            return ForgejoCommitFlag(
                project=project,
                raw_commit_flag=status,
                commit=commit,
            )

        except pyforgejo.NotFoundError as ex:  # 404 error
            logger.error(f"Commit {commit} was not found.")
            raise ForgejoAPIException(f"Commit {commit} was not found.") from ex

    @property
    def created(self) -> datetime.datetime:
        return self._raw_commit_flag.created_at

    @property
    def edited(self) -> datetime.datetime:
        return self._raw_commit_flag.updated_at

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from collections.abc import Iterable
from typing import Any, ClassVar, Optional, Union

from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.git_project import GitProject
from ogr.abstract.status import CommitStatus


class CommitFlag(OgrAbstractClass):
    _states: ClassVar[dict[str, CommitStatus]] = {}

    def __init__(
        self,
        raw_commit_flag: Optional[Any] = None,
        project: Optional["GitProject"] = None,
        commit: Optional[str] = None,
        state: Optional[CommitStatus] = None,
        context: Optional[str] = None,
        comment: Optional[str] = None,
        uid: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        self.uid = uid
        self.project = project
        self.commit = commit

        if commit and state and context:
            self.state = state
            self.context = context
            self.comment = comment
            self.url = url
        else:
            self._raw_commit_flag = raw_commit_flag
            self._from_raw_commit_flag()

    def __str__(self) -> str:
        return (
            f"CommitFlag("
            f"commit='{self.commit}', "
            f"state='{self.state.name}', "
            f"context='{self.context}', "
            f"uid='{self.uid}', "
            f"comment='{self.comment}', "
            f"url='{self.url}', "
            f"created='{self.created}', "
            f"edited='{self.edited}')"
        )

    @classmethod
    def _state_from_str(cls, state: str) -> CommitStatus:
        """
        Transforms state from string to enumeration.

        Args:
            state: String representation of a state.

        Returns:
            Commit status.
        """
        raise NotImplementedError()

    @classmethod
    def _validate_state(cls, state: CommitStatus) -> CommitStatus:
        """
        Validates state of the commit status (if it can be used with forge).
        """
        raise NotImplementedError()

    def _from_raw_commit_flag(self) -> None:
        """
        Sets attributes based on the raw flag that has been given through constructor.
        """
        raise NotImplementedError()

    @staticmethod
    def get(
        project: Any,
        commit: str,
    ) -> Union[list["CommitFlag"], Iterable["CommitFlag"]]:
        """
        Acquire commit statuses for given commit in the project.

        Args:
            project (GitProject): Project where the commit is located.
            commit: Commit hash for which we request statuses.

        Returns:
            List of commit statuses for the commit.
        """
        raise NotImplementedError()

    @staticmethod
    def set(
        project: Any,
        commit: str,
        state: CommitStatus,
        target_url: str,
        description: str,
        context: str,
    ) -> "CommitFlag":
        """
        Set a new commit status.

        Args:
            project (GitProject): Project where the commit is located.
            commit: Commit hash for which we set status.
            state: State for the commit status.
            target_url: URL for the commit status.
            description: Description of the commit status.
            context: Identifier to group related commit statuses.
        """
        raise NotImplementedError()

    @property
    def created(self) -> datetime.datetime:
        """Datetime of creating the commit status."""
        raise NotImplementedError()

    @property
    def edited(self) -> datetime.datetime:
        """Datetime of editing the commit status."""
        raise NotImplementedError()

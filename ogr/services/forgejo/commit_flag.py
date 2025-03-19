# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Any

from pyforgejo import PyforgejoApi

from ogr.abstract import CommitFlag, CommitStatus


class ForgejoCommitFlag(CommitFlag):
    """
    CommitFlag implementation for Forgejo.
    """

    @classmethod
    def _state_from_str(cls, state: str) -> CommitStatus:
        # Convert a status string returned by Forgejo API into CommitStatus enum.
        state = state.lower()
        if state == "success":
            return CommitStatus.success
        if state == "failure":
            return CommitStatus.failure
        if state == "pending":
            return CommitStatus.pending
        raise ValueError(f"Unknown commit state from Forgejo: {state}")

    @classmethod
    def _validate_state(cls, state: CommitStatus) -> CommitStatus:
        # Validate that the provided state is acceptable for Forgejo.
        valid_states = {
            CommitStatus.success,
            CommitStatus.failure,
            CommitStatus.pending,
        }
        if state in valid_states:
            return state
        raise ValueError(f"Invalid commit state for Forgejo: {state}")

    def _from_raw_commit_flag(self) -> None:
        """
        Populate attributes from the raw commit flag data obtained from Forgejo's API.
        Expected keys in self._raw_commit_flag: 'commit', 'state', 'context', 'comment', 'id',
        'created', and 'updated'.
        """
        raw = self._raw_commit_flag
        self.commit = raw.get("commit")
        self.state = self._state_from_str(raw.get("state", "pending"))
        self.context = raw.get("context")
        self.comment = raw.get("comment")
        self.uid = raw.get("id")
        self.url = raw.get("url")
        self._created = raw.get("created")
        self._edited = raw.get("updated")

    @staticmethod
    def get(project: Any, commit: str) -> list["CommitFlag"]:
        """
        Retrieve commit statuses for the given commit from Forgejo using the pyforgejo SDK.
        """
        client = PyforgejoApi(api_url=project.forge_api_url, token=project.token)
        raw_flags = client.get_commit_statuses(
            owner=project.owner,
            repo=project.repo,
            commit=commit,
        )
        return [
            ForgejoCommitFlag(raw_commit_flag=raw_flag, project=project, commit=commit)
            for raw_flag in raw_flags
        ]

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
        Set a new commit status on Forgejo via the pyforgejo SDK.
        """
        client = PyforgejoApi(api_url=project.forge_api_url, token=project.token)
        raw_response = client.set_commit_status(
            owner=project.owner,
            repo=project.repo,
            commit=commit,
            state=state.name.lower(),
            target_url=target_url,
            description=description,
            context=context,
        )
        return ForgejoCommitFlag(
            raw_commit_flag=raw_response,
            project=project,
            commit=commit,
        )

    @property
    def created(self) -> datetime:
        return self._created

    @property
    def edited(self) -> datetime:
        return self._edited

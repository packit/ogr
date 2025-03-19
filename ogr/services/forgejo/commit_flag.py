# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Any

import requests

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
        # Parse timestamps in ISO8601 format (adjust format if needed)
        self._created = datetime.strptime(raw.get("created"), "%Y-%m-%dT%H:%M:%SZ")
        self._edited = datetime.strptime(raw.get("updated"), "%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def get(project: Any, commit: str) -> list["CommitFlag"]:
        """
        Retrieve commit statuses for the given commit from Forgejo.
        This method should use Forgejo's API to fetch statuses.
        """
        # Construct the URL using the project's forge_api_url, owner, repo, and commit hash.
        url = (
            f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/commits/"
            f"{commit}/statuses"
        )
        headers = project.get_auth_header()  # Get auth headers from project config
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        flags: list[CommitFlag] = [
            ForgejoCommitFlag(raw_commit_flag=raw_flag, project=project, commit=commit)
            for raw_flag in response.json()
        ]
        return flags

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
        Set a new commit status on Forgejo via its API.
        """
        url = (
            f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/commits/"
            f"{commit}/statuses"
        )
        payload = {
            "state": state.name.lower(),
            "target_url": target_url,
            "description": description,
            "context": context,
        }
        headers = project.get_auth_header()
        response = requests.post(url, json=payload, headers=headers)
        return ForgejoCommitFlag(
            raw_commit_flag=response.json(),
            project=project,
            commit=commit,
        )

    @property
    def created(self) -> datetime:
        return self._created

    @property
    def edited(self) -> datetime:
        return self._edited

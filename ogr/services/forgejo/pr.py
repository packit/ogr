# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import Any, Optional

from ogr.abstract import GitProject, MergeCommitStatus, PRLabel, PRStatus, PullRequest


class ForgejoPullRequest(PullRequest):
    """
    Implementation of PullRequest for Forgejo.
    """

    def __init__(self, raw_pr: Any, project: "GitProject") -> None:
        super().__init__(raw_pr, project)

    @property
    def title(self) -> str:
        return self._raw_pr["title"]

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_pr["title"] = new_title

    @property
    def id(self) -> int:
        return self._raw_pr["id"]

    @property
    def status(self) -> PRStatus:
        status_value = self._raw_pr.get("status") or self._raw_pr.get("state")
        if not status_value:
            raise KeyError("Neither 'status' nor 'state' key found in PR data.")
        for member in PRStatus:
            if member.name.lower() == status_value.lower():
                return member
        raise ValueError(f"Invalid PR status: {status_value}")

    @property
    def url(self) -> str:
        return self._raw_pr.get("url") or self._raw_pr.get("html_url", "")

    @property
    def description(self) -> str:
        return self._raw_pr.get("body", "")

    @description.setter
    def description(self, new_description: str) -> None:
        self._raw_pr["description"] = new_description

    @property
    def author(self) -> str:
        return self._raw_pr.get("author") or self._raw_pr.get("user", {}).get(
            "login",
            "",
        )

    @property
    def source_branch(self) -> str:
        return self._raw_pr.get("source_branch") or self._raw_pr.get("head", {}).get(
            "ref",
            "",
        )

    @property
    def source_project(self) -> "GitProject":
        return self._target_project

    @property
    def target_branch(self) -> str:
        return self._raw_pr.get("target_branch") or self._raw_pr.get("base", {}).get(
            "ref",
            "",
        )

    @property
    def created(self) -> datetime.datetime:
        created_str = self._raw_pr.get("created") or self._raw_pr.get("created_at")
        if not created_str:
            raise KeyError("Missing 'created' or 'created_at' key in PR data")
        return datetime.datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%SZ")

    @property
    def labels(self) -> list[PRLabel]:
        return [PRLabel(label) for label in self._raw_pr.get("labels", [])]

    @property
    def diff_url(self) -> str:
        return self._raw_pr["diff_url"]

    @property
    def patch(self) -> bytes:
        return self._raw_pr.get("patch", b"")

    @property
    def head_commit(self) -> str:
        return self._raw_pr["head_commit"]

    @property
    def merge_commit_sha(self) -> str:
        return self._raw_pr.get("merge_commit_sha", "")

    @property
    def merge_commit_status(self) -> MergeCommitStatus:
        return MergeCommitStatus[
            self._raw_pr.get("merge_commit_status", "unknown").upper()
        ]

    @staticmethod
    def create(
        project: Any,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> "ForgejoPullRequest":
        """
        Create a new pull request in Forgejo.
        """
        pr_data = {
            "title": title,
            "body": body,
            "target_branch": target_branch,
            "source_branch": source_branch,
        }
        raw_pr = project.create_pull_request(pr_data)  # Simulated API call
        return ForgejoPullRequest(raw_pr, project)

    def merge(self) -> "ForgejoPullRequest":
        """Merge the pull request."""
        self._raw_pr["status"] = "merged"
        return self

    def close(self) -> "ForgejoPullRequest":
        """Close the pull request."""
        self._raw_pr["status"] = "closed"
        return self

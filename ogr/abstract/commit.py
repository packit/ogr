# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from typing import Any, Union

from ogr import abstract as _abstract
from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.git_project import GitProject


class GitCommit(OgrAbstractClass):
    """
    Class representing a git commit

    Attributes:
        project (GitProject): Git project where the commit belongs to.
    """

    def __init__(self, raw_commit: Any, project: "GitProject") -> None:
        self._raw_commit = raw_commit
        self.project = project

    @property
    def sha(self) -> str:
        """Commit hash."""
        raise NotImplementedError()

    @property
    def changes(self) -> "CommitChanges":
        """Commit change information."""
        raise NotImplementedError()

    def get_prs(self) -> Iterable["_abstract.PullRequest"]:
        """Get the associated pull requests"""
        raise NotImplementedError()


class CommitLikeChanges(OgrAbstractClass):
    """
    Class representing a commit-like changes.

    Can be from a single commit or aggregated like from a PR.
    """

    @property
    def parent(self) -> Union["GitCommit", "_abstract.PullRequest"]:
        """Parent object containing the changes."""
        raise NotImplementedError()

    @property
    def files(self) -> Union[list[str], Iterable[str]]:
        """Files changed by the current change."""
        raise NotImplementedError()

    @property
    def patch(self) -> bytes:
        """Patch of the changes."""
        raise NotImplementedError()

    @property
    def diff_url(self) -> str:
        """Web URL to the diff of the pull request."""
        raise NotImplementedError()


class CommitChanges(CommitLikeChanges):
    """
    Class representing a Commit's change

    Attributes:
        commit (GitCommit): Parent commit.
    """

    def __init__(self, commit: "GitCommit") -> None:
        self.commit = commit

    @property
    def parent(self) -> "GitCommit":
        return self.commit

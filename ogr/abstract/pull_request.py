# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from collections.abc import Iterable
from re import Match
from typing import Any, Optional, Union

from ogr import abstract as _abstract
from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.commit_flag import CommitFlag
from ogr.abstract.git_project import GitProject
from ogr.abstract.status import MergeCommitStatus, PRStatus


class PullRequest(OgrAbstractClass):
    """
    Attributes:
        project (GitProject): Project of the pull request.
    """

    def __init__(self, raw_pr: Any, project: "GitProject") -> None:
        self._raw_pr = raw_pr
        self._target_project = project

    @property
    def title(self) -> str:
        """Title of the pull request."""
        raise NotImplementedError()

    @title.setter
    def title(self, new_title: str) -> None:
        raise NotImplementedError()

    @property
    def id(self) -> int:
        """ID of the pull request."""
        raise NotImplementedError()

    @property
    def status(self) -> PRStatus:
        """Status of the pull request."""
        raise NotImplementedError()

    @property
    def url(self) -> str:
        """Web URL of the pull request."""
        raise NotImplementedError()

    @property
    def description(self) -> str:
        """Description of the pull request."""
        raise NotImplementedError()

    @description.setter
    def description(self, new_description: str) -> None:
        raise NotImplementedError

    @property
    def author(self) -> str:
        """Login of the author of the pull request."""
        raise NotImplementedError()

    @property
    def source_branch(self) -> str:
        """Name of the source branch (from which the changes are pulled)."""
        raise NotImplementedError()

    @property
    def target_branch(self) -> str:
        """Name of the target branch (where the changes are being merged)."""
        raise NotImplementedError()

    @property
    def created(self) -> datetime.datetime:
        """Datetime of creating the pull request."""
        raise NotImplementedError()

    @property
    def labels(self) -> Union[list["_abstract.PRLabel"], Iterable["_abstract.PRLabel"]]:
        """Labels of the pull request."""
        raise NotImplementedError()

    @property
    def diff_url(self) -> str:
        """Web URL to the diff of the pull request."""
        raise NotImplementedError()

    @property
    def patch(self) -> bytes:
        """Patch of the pull request."""
        raise NotImplementedError()

    @property
    def head_commit(self) -> str:
        """Commit hash of the HEAD commit of the pull request."""
        raise NotImplementedError()

    @property
    def target_branch_head_commit(self) -> str:
        """Commit hash of the HEAD commit of the target branch."""
        raise NotImplementedError()

    @property
    def merge_commit_sha(self) -> str:
        """
        Commit hash of the merge commit of the pull request.

        Before merging represents test merge commit, if git forge supports it.
        """
        raise NotImplementedError()

    @property
    def merge_commit_status(self) -> MergeCommitStatus:
        """Current status of the test merge commit."""
        raise NotImplementedError()

    @property
    def source_project(self) -> "GitProject":
        """Object that represents source project (from which the changes are pulled)."""
        raise NotImplementedError()

    @property
    def target_project(self) -> "GitProject":
        """Object that represents target project (where changes are merged)."""
        return self._target_project

    @property
    def commits_url(self) -> str:
        """Web URL to the list of commits in the pull request."""
        raise NotImplementedError()

    @property
    def closed_by(self) -> Optional[str]:
        """Login of the account that closed the pull request."""
        raise NotImplementedError()

    def __str__(self) -> str:
        description = (
            f"{self.description[:10]}..." if self.description is not None else "None"
        )
        return (
            f"PullRequest("
            f"title='{self.title}', "
            f"id={self.id}, "
            f"status='{self.status.name}', "
            f"url='{self.url}', "
            f"diff_url='{self.diff_url}', "
            f"description='{description}', "
            f"author='{self.author}', "
            f"source_branch='{self.source_branch}', "
            f"target_branch='{self.target_branch}', "
            f"created='{self.created}')"
        )

    @staticmethod
    def create(
        project: Any,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> "PullRequest":
        """
        Create new pull request.

        Args:
            project (GitProject): Project where the pull request will be created.
            title: Title of the pull request.
            body: Description of the pull request.
            target_branch: Branch in the project where the changes are being
                merged.
            source_branch: Branch from which the changes are being pulled.
            fork_username: The username/namespace of the forked repository.

        Returns:
            Object that represents newly created pull request.
        """
        raise NotImplementedError()

    @staticmethod
    def get(project: Any, id: int) -> "PullRequest":
        """
        Get pull request.

        Args:
            project (GitProject): Project where the pull request is located.
            id: ID of the pull request.

        Returns:
            Object that represents pull request.
        """
        raise NotImplementedError()

    @staticmethod
    def get_list(
        project: Any,
        status: PRStatus = PRStatus.open,
    ) -> Union[list["PullRequest"], Iterable["PullRequest"]]:
        """
        List of pull requests.

        Args:
            project (GitProject): Project where the pull requests are located.
            status: Filters out the pull requests.

                Defaults to `PRStatus.open`.

        Returns:
            List of pull requests with requested status.
        """
        raise NotImplementedError()

    def update_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PullRequest":
        """
        Update pull request information.

        Args:
            title: The new title of the pull request.

                Defaults to `None`, which means no updating.
            description: The new description of the pull request.

                Defaults to `None`, which means no updating.

        Returns:
            Pull request itself.
        """
        raise NotImplementedError()

    def _get_all_comments(
        self,
        reverse: bool = False,
    ) -> Union[list["_abstract.PRComment"], Iterable["_abstract.PRComment"]]:
        """
        Get list of all pull request comments.

        Args:
            reverse: Defines whether the comments should be listed in a reversed
                order.

                Defaults to `False`.

        Returns:
            List of all comments on the pull request.
        """
        raise NotImplementedError()

    def get_comments(
        self,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> Union[list["_abstract.PRComment"], Iterable["_abstract.PRComment"]]:
        """
        Get list of pull request comments.

        Args:
            filter_regex: Filter the comments' content with `re.search`.

                Defaults to `None`, which means no filtering.
            reverse: Whether the comments are to be returned in
                reversed order.

                Defaults to `False`.
            author: Filter the comments by author.

                Defaults to `None`, which means no filtering.

        Returns:
            List of pull request comments.
        """
        raise NotImplementedError()

    def get_all_commits(self) -> Union[list[str], Iterable[str]]:
        """
        Returns:
            List of commit hashes of commits in pull request.
        """
        raise NotImplementedError()

    def search(
        self,
        filter_regex: str,
        reverse: bool = False,
        description: bool = True,
    ) -> Optional[Match[str]]:
        """
        Find match in pull request description or comments.

        Args:
            filter_regex: Regex that is used to filter the comments' content with `re.search`.
            reverse: Reverse order of the comments.

                Defaults to `False`.
            description: Whether description is included in the search.

                Defaults to `True`.

        Returns:
            `re.Match` if found, `None` otherwise.
        """
        raise NotImplementedError()

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "_abstract.PRComment":
        """
        Add new comment to the pull request.

        Args:
            body: Body of the comment.
            commit: Commit hash to which comment is related.

                Defaults to generic comment.
            filename: Path to the file to which comment is related.

                Defaults to no relation to the file.
            row: Line number to which the comment is related.

                Defaults to no relation to the line.

        Returns:
            Newly created comment.
        """
        raise NotImplementedError()

    def close(self) -> "PullRequest":
        """
        Close the pull request.

        Returns:
            Pull request itself.
        """
        raise NotImplementedError()

    def merge(self) -> "PullRequest":
        """
        Merge the pull request.

        Returns:
            Pull request itself.
        """
        raise NotImplementedError()

    def add_label(self, *labels: str) -> None:
        """
        Add labels to the pull request.

        Args:
            *labels: Labels to be added.
        """
        raise NotImplementedError()

    def get_statuses(self) -> Union[list["CommitFlag"], Iterable["CommitFlag"]]:
        """
        Returns statuses for latest commit on pull request.

        Returns:
            List of commit statuses of the latest commit.
        """
        raise NotImplementedError()

    def get_comment(self, comment_id: int) -> "_abstract.PRComment":
        """
        Returns a PR comment.

        Args:
            comment_id: id of comment

        Returns:
            Object representing a PR comment.
        """
        raise NotImplementedError()

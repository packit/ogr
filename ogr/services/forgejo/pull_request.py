# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
import datetime
import logging
from collections.abc import Iterable
from functools import cached_property, partial
from typing import Optional, Union

import httpx
from pyforgejo import NotFoundError
from pyforgejo.types import PullRequest as PyforgejoPullRequest

from ogr.abstract import (
    CommitFlag,
    MergeCommitStatus,
    PRComment,
    PRLabel,
    PRStatus,
    PullRequest,
)
from ogr.exceptions import ForgejoAPIException, OgrNetworkError
from ogr.services import forgejo
from ogr.services.base import BasePullRequest
from ogr.services.forgejo.label import ForgejoPRLabel
from ogr.services.forgejo.utils import paginate

logger = logging.getLogger(__name__)


class ForgejoPullRequest(BasePullRequest):
    _target_project: "forgejo.ForgejoProject" = None
    _source_project: "forgejo.ForgejoProject" = None
    _labels: list[PRLabel] = None

    def __init__(
        self,
        raw_pr: PyforgejoPullRequest,
        project: "forgejo.ForgejoProject",
    ):
        super().__init__(raw_pr, project)

    def __str__(self) -> str:
        return "Forgejo" + super().__str__()

    @property
    def title(self) -> str:
        return self._raw_pr.title

    @title.setter
    def title(self, new_title: str) -> None:
        self.update_info(title=new_title)

    @property
    def id(self) -> int:
        return self._raw_pr.number

    @property
    def status(self) -> PRStatus:
        return PRStatus.merged if self._raw_pr.merged else PRStatus[self._raw_pr.state]

    @property
    def url(self) -> str:
        return self._raw_pr.url

    @property
    def description(self) -> str:
        return self._raw_pr.body

    @description.setter
    def description(self, new_description: str) -> None:
        self.update_info(description=new_description)

    @property
    def author(self) -> str:
        return self._raw_pr.user.login

    @property
    def source_branch(self) -> str:
        return self._raw_pr.head.ref

    @property
    def target_branch(self) -> str:
        return self._raw_pr.base.ref

    @property
    def created(self) -> datetime.datetime:
        return self._raw_pr.created_at

    @property
    def labels(self) -> list[PRLabel]:
        if not self._labels:
            self._labels = (
                [ForgejoPRLabel(raw_label, self) for raw_label in self._raw_pr.labels]
                if self._raw_pr.labels
                else []
            )
        return self._labels

    @property
    def diff_url(self) -> str:
        return self._raw_pr.diff_url

    @property
    def patch(self) -> bytes:
        patch_url = self._raw_pr.patch_url
        response = httpx.get(patch_url)

        if not response.is_success:
            raise OgrNetworkError(
                f"Couldn't get patch from {patch_url}.patch because {response.reason}.",
            )

        return response.content

    @property
    def head_commit(self) -> str:
        return self._raw_pr.head.sha

    @property
    def merge_commit_sha(self) -> Optional[str]:
        # this is None for non-merged PRs
        return self._raw_pr.merge_commit_sha

    @property
    def merge_commit_status(self) -> MergeCommitStatus:
        return (
            MergeCommitStatus.can_be_merged
            if self._raw_pr.mergeable
            else MergeCommitStatus.cannot_be_merged
        )

    @cached_property
    def source_project(self) -> "forgejo.ForgejoProject":
        pyforgejo_repo = self._raw_pr.head.repo
        return self._target_project.service.get_project(
            repo=pyforgejo_repo.name,
            namespace=pyforgejo_repo.owner.login,
            forgejo_repo=pyforgejo_repo,
        )

    @property
    def commits_url(self) -> str:
        return f"{self.url}/commits"

    @property
    def closed_by(self) -> Optional[str]:
        return self._raw_pr.merged_by.login if self._raw_pr.merged_by else None

    @staticmethod
    def create(
        project: "forgejo.ForgejoProject",
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> "PullRequest":
        target_project = project

        if project.is_fork and fork_username is None:
            # handles fork -> upstream (called on fork)
            source_branch = f"{project.namespace}:{source_branch}"
            target_project = project.parent  # type: ignore
        elif fork_username:
            if fork_username != project.namespace and project.parent is not None:
                # handles fork -> other_fork
                #   (username of other_fork owner specified by fork_username)
                forks = list(
                    filter(
                        lambda fork: fork.namespace == fork_username,
                        project.parent.get_forks(),
                    ),
                )
                if not forks:
                    raise ForgejoAPIException("Requested fork doesn't exist")
                target_project = forks[0]  # type: ignore
                source_branch = f"{project.namespace}:{source_branch}"
            else:
                # handles fork -> upstream
                #   (username of fork owner specified by fork_username)
                source_branch = f"{fork_username}:{source_branch}"

        logger.debug(f"Creating PR {target_branch}<-{source_branch}")

        pr = target_project.api.repo_create_pull_request(
            owner=target_project.namespace,
            repo=target_project.repo,
            base=target_branch,
            body=body,
            head=source_branch,
            title=title,
        )
        logger.info(f"PR {pr.id} created.")

        return ForgejoPullRequest(pr, target_project)

    @staticmethod
    def get(project: "forgejo.ForgejoProject", pr_id: int) -> "PullRequest":
        try:
            raw_pr = project.api.repo_get_pull_request(
                owner=project.namespace,
                repo=project.repo,
                index=pr_id,
            )
        except NotFoundError as ex:
            raise ForgejoAPIException(f"No pull request with id {pr_id} found.") from ex
        return ForgejoPullRequest(raw_pr, project)

    @staticmethod
    def get_list(
        project: "forgejo.ForgejoProject",
        status: PRStatus = PRStatus.open,
    ) -> Iterable["PullRequest"]:
        prs = paginate(
            partial(
                project.api.repo_list_pull_requests,
                owner=project.namespace,
                repo=project.repo,
                # Forgejo has just open/closed/all
                state=status.name if status != PRStatus.merged else "closed",
            ),
        )
        return (ForgejoPullRequest(pr, project) for pr in prs)

    def update_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PullRequest":
        try:
            data = {"title": title if title else self.title}

            if description is not None:
                data["body"] = description

            updated_pr = self._target_project.api.repo_edit_pull_request(
                owner=self.target_project.namespace,
                repo=self.target_project.repo,
                index=self.id,
                **data,
            )

            self._raw_pr = updated_pr
            return self
        except Exception as ex:
            raise ForgejoAPIException(
                f"There was an error while updating Forgejo PR: {ex}",
            ) from ex

    def close(self) -> "PullRequest":
        self._raw_pr = self._target_project.api.repo_edit_pull_request(
            owner=self.target_project.namespace,
            repo=self.target_project.repo,
            index=self.id,
            state="closed",
        )
        return self

    def merge(self) -> "PullRequest":
        self._target_project.api.repo_merge_pull_request(
            owner=self.target_project.namespace,
            repo=self.target_project.repo,
            index=self.id,
            # options: merge, rebase, rebase-merge, squash, fast-forward-only, manually-merged
            do="merge",
        )
        return self.get(self._target_project, self.id)

    def add_label(self, *labels: str) -> None:
        issue_client = self._target_project.service.api.issue
        new_labels = issue_client.add_label(
            owner=self.target_project.namespace,
            repo=self.target_project.repo,
            index=self.id,
            labels=list(labels),
        )
        self._labels = [ForgejoPRLabel(raw_label, self) for raw_label in new_labels]

    def get_all_commits(self) -> Iterable[str]:
        return (
            commit.sha
            for commit in paginate(
                partial(
                    self._target_project.api.repo_get_pull_request_commits,
                    owner=self.target_project.namespace,
                    repo=self.target_project.repo,
                    index=self.id,
                ),
            )
        )

    def get_comments(
        self,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> Union[list["PRComment"], Iterable["PRComment"]]:
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

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
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

    def get_comment(self, comment_id: int) -> PRComment:
        """
        Returns a PR comment.

        Args:
            comment_id: id of comment

        Returns:
            Object representing a PR comment.
        """
        raise NotImplementedError()

    def get_statuses(self) -> Union[list[CommitFlag], Iterable[CommitFlag]]:
        """
        Returns statuses for latest commit on pull request.

        Returns:
            List of commit statuses of the latest commit.
        """
        raise NotImplementedError()

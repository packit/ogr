# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import logging
from typing import Optional, Union

import github
import requests
from github import UnknownObjectException
from github.IssueComment import IssueComment as _GithubIssueComment
from github.PullRequest import PullRequest as _GithubPullRequest
from github.PullRequestComment import PullRequestComment as _GithubPullRequestComment
from github.Repository import Repository as _GithubRepository

from ogr.abstract import MergeCommitStatus, PRComment, PRLabel, PRStatus, PullRequest
from ogr.exceptions import GithubAPIException, OgrNetworkError
from ogr.services import github as ogr_github
from ogr.services.base import BasePullRequest
from ogr.services.github.comments import GithubPRComment
from ogr.services.github.label import GithubPRLabel

logger = logging.getLogger(__name__)


class GithubPullRequest(BasePullRequest):
    _raw_pr: _GithubPullRequest
    _target_project: "ogr_github.GithubProject"
    _source_project: "ogr_github.GithubProject" = None

    @property
    def title(self) -> str:
        return self._raw_pr.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_pr.edit(title=new_title)

    @property
    def id(self) -> int:
        return self._raw_pr.number

    @property
    def status(self) -> PRStatus:
        return (
            PRStatus.merged
            if self._raw_pr.is_merged()
            else PRStatus[self._raw_pr.state]
        )

    @property
    def url(self) -> str:
        return self._raw_pr.html_url

    @property
    def description(self) -> str:
        return self._raw_pr.body

    @description.setter
    def description(self, new_description: str) -> None:
        self._raw_pr.edit(body=new_description)

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
        return [
            GithubPRLabel(raw_label, self) for raw_label in self._raw_pr.get_labels()
        ]

    @property
    def diff_url(self) -> str:
        return f"{self._raw_pr.html_url}/files"

    @property
    def patch(self) -> bytes:
        response = requests.get(self._raw_pr.patch_url)

        if not response.ok:
            cls = OgrNetworkError if response.status_code >= 500 else GithubAPIException
            raise cls(
                f"Couldn't get patch from {self._raw_pr.patch_url} because {response.reason}.",
            )

        return response.content

    @property
    def commits_url(self) -> str:
        return f"{self._raw_pr.html_url}/commits"

    @property
    def head_commit(self) -> str:
        return self._raw_pr.head.sha

    @property
    def merge_commit_sha(self) -> str:
        return self._raw_pr.merge_commit_sha

    @property
    def merge_commit_status(self) -> MergeCommitStatus:
        if self._raw_pr.mergeable:
            return MergeCommitStatus.can_be_merged

        return MergeCommitStatus.cannot_be_merged

    @property
    def source_project(self) -> "ogr_github.GithubProject":
        if self._source_project is None:
            self._source_project = (
                self._target_project.service.get_project_from_github_repository(
                    self._raw_pr.head.repo,
                )
            )

        return self._source_project

    def __str__(self) -> str:
        return "Github" + super().__str__()

    @staticmethod
    def create(
        project: "ogr_github.GithubProject",
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> "PullRequest":
        """
        The default behavior is the pull request is made to the immediate parent repository
        if the repository is a forked repository.
        If you want to create a pull request to the forked repo, please pass
        the `fork_username` parameter.
        """
        github_repo = project.github_repo

        target_project = project
        if project.is_fork and fork_username is None:
            logger.warning(f"{project.full_repo_name} is fork, ignoring fork_repo.")
            source_branch = f"{project.namespace}:{source_branch}"
            github_repo = project.parent.github_repo
            target_project = project.parent
        elif fork_username:
            source_branch = f"{fork_username}:{source_branch}"
            if fork_username != project.namespace and project.parent is not None:
                github_repo = GithubPullRequest.__get_fork(
                    fork_username,
                    project.parent.github_repo,
                )

        created_pr = github_repo.create_pull(
            title=title,
            body=body,
            base=target_branch,
            head=source_branch,
        )
        logger.info(f"PR {created_pr.id} created: {target_branch}<-{source_branch}")
        return GithubPullRequest(created_pr, target_project)

    @staticmethod
    def __get_fork(fork_username: str, repo: _GithubRepository) -> _GithubRepository:
        forks = list(
            filter(lambda fork: fork.owner.login == fork_username, repo.get_forks()),
        )
        if not forks:
            raise GithubAPIException("Requested fork doesn't exist")
        return forks[0]

    @staticmethod
    def get(project: "ogr_github.GithubProject", pr_id: int) -> "PullRequest":
        try:
            pr = project.github_repo.get_pull(number=pr_id)
        except github.UnknownObjectException as ex:
            raise GithubAPIException(f"No pull request with id {pr_id} found") from ex
        return GithubPullRequest(pr, project)

    @staticmethod
    def get_list(
        project: "ogr_github.GithubProject",
        status: PRStatus = PRStatus.open,
    ) -> list["PullRequest"]:
        prs = project.github_repo.get_pulls(
            # Github API has no status 'merged', just 'closed'/'opened'/'all'
            state=status.name if status != PRStatus.merged else "closed",
            sort="updated",
            direction="desc",
        )

        if status == PRStatus.merged:
            prs = list(prs)  # Github PaginatedList into list()
            for pr in prs:
                if not pr.is_merged():  # parse merged PRs
                    prs.remove(pr)
        try:
            return [GithubPullRequest(pr, project) for pr in prs]
        except UnknownObjectException:
            return []

    def update_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PullRequest":
        try:
            self._raw_pr.edit(title=title, body=description)
            logger.info(f"PR updated: {self._raw_pr.url}")
            return self
        except Exception as ex:
            raise GithubAPIException("there was an error while updating the PR") from ex

    def _get_all_comments(self) -> list[PRComment]:
        return [
            GithubPRComment(parent=self, raw_comment=raw_comment)
            for raw_comment in self._raw_pr.get_issue_comments()
        ]

    def get_all_commits(self) -> list[str]:
        return [commit.sha for commit in self._raw_pr.get_commits()]

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
        comment: Union[_GithubIssueComment, _GithubPullRequestComment] = None
        if not any([commit, filename, row]):
            comment = self._raw_pr.create_issue_comment(body)
        else:
            github_commit = self._target_project.github_repo.get_commit(commit)
            comment = self._raw_pr.create_comment(body, github_commit, filename, row)
        return GithubPRComment(parent=self, raw_comment=comment)

    def close(self) -> "PullRequest":
        self._raw_pr.edit(state=PRStatus.closed.name)
        return self

    def merge(self) -> "PullRequest":
        self._raw_pr.merge()
        return self

    def add_label(self, *labels: str) -> None:
        for label in labels:
            self._raw_pr.add_to_labels(label)

    def get_comment(self, comment_id: int) -> PRComment:
        return GithubPRComment(self._raw_pr.get_issue_comment(comment_id))

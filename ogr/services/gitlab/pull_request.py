# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime

import gitlab
import requests
from typing import Dict, List, Optional

from gitlab.v4.objects import MergeRequest as _GitlabMergeRequest
from gitlab.exceptions import GitlabGetError

from ogr.abstract import PullRequest, PRComment, PRStatus, MergeCommitStatus
from ogr.exceptions import GitlabAPIException, OgrNetworkError
from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BasePullRequest
from ogr.services.gitlab.comments import GitlabPRComment


class GitlabPullRequest(BasePullRequest):
    _raw_pr: _GitlabMergeRequest
    _target_project: "ogr_gitlab.GitlabProject"
    _source_project: Optional["ogr_gitlab.GitlabProject"] = None
    _merge_commit_status: Dict[str, MergeCommitStatus] = {
        "can_be_merged": MergeCommitStatus.can_be_merged,
        "cannot_be_merged": MergeCommitStatus.cannot_be_merged,
        "unchecked": MergeCommitStatus.unchecked,
        "checking": MergeCommitStatus.checking,
        "cannot_be_merged_recheck": MergeCommitStatus.cannot_be_merged_recheck,
    }

    @property
    def title(self) -> str:
        return self._raw_pr.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_pr.title = new_title
        self._raw_pr.save()

    @property
    def id(self) -> int:
        return self._raw_pr.iid

    @property
    def status(self) -> PRStatus:
        return (
            PRStatus.open
            if self._raw_pr.state == "opened"
            else PRStatus[self._raw_pr.state]
        )

    @property
    def url(self) -> str:
        return self._raw_pr.web_url

    @property
    def description(self) -> str:
        return self._raw_pr.description

    @description.setter
    def description(self, new_description: str) -> None:
        self._raw_pr.description = new_description
        self._raw_pr.save()

    @property
    def author(self) -> str:
        return self._raw_pr.author["username"]

    @property
    def source_branch(self) -> str:
        return self._raw_pr.source_branch

    @property
    def target_branch(self) -> str:
        return self._raw_pr.target_branch

    @property
    def created(self) -> datetime.datetime:
        return self._raw_pr.created_at

    @property
    def labels(self) -> List[str]:
        return self._raw_pr.labels

    @property
    def diff_url(self) -> str:
        return f"{self._raw_pr.web_url}/diffs"

    @property
    def commits_url(self) -> str:
        return f"{self._raw_pr.web_url}/commits"

    @property
    def patch(self) -> bytes:
        response = requests.get(f"{self.url}.patch")

        if not response.ok:
            cls = OgrNetworkError if response.status_code >= 500 else GitlabAPIException
            raise cls(
                f"Couldn't get patch from {self.url}.patch because {response.reason}."
            )

        return response.content

    @property
    def head_commit(self) -> str:
        return self._raw_pr.sha

    @property
    def merge_commit_sha(self) -> Optional[str]:
        # when merged => return merge_commit_sha
        # otherwise => return test merge if possible
        if self.status == PRStatus.merged:
            return self._raw_pr.merge_commit_sha

        # works for test merge only with python-gitlab>=2.10.0
        try:
            response = self._raw_pr.merge_ref()
        except GitlabGetError as ex:
            if ex.response_code == 400:
                return None
            raise
        return response.get("commit_id")

    @property
    def merge_commit_status(self) -> MergeCommitStatus:
        status = self._raw_pr.merge_status
        if status in self._merge_commit_status:
            return self._merge_commit_status[status]
        else:
            raise GitlabAPIException(f"Invalid merge_status {status}")

    @property
    def source_project(self) -> "ogr_gitlab.GitlabProject":
        if self._source_project is None:
            self._source_project = (
                self._target_project.service.get_project_from_project_id(
                    self._raw_pr.attributes["source_project_id"]
                )
            )
        return self._source_project

    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

    @staticmethod
    def create(
        project: "ogr_gitlab.GitlabProject",
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        """
        How to create PR:
        -  upstream -> upstream - call on upstream, fork_username unset
        -  fork -> upstream - call on fork, fork_username unset
           also can call on upstream with fork_username, not supported way of using
        -  fork -> fork - call on fork, fork_username set
        -  fork -> other_fork - call on fork, fork_username set to other_fork owner
        """
        repo = project.gitlab_repo
        parameters = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": body,
        }
        target_id = None

        target_project = project
        if project.parent and project.is_fork and fork_username is None:
            # handles fork -> upstream (called on fork)
            target_id = project.parent.gitlab_repo.attributes["id"]
            target_project = project.parent
        elif fork_username and fork_username != project.namespace:
            # handles fork -> upstream
            #   (username of fork owner specified by fork_username)
            # handles fork -> other_fork
            #   (username of other_fork owner specified by fork_username)

            other_project = GitlabPullRequest.__get_fork(
                fork_username,
                project if project.parent is None else project.parent,
            )

            target_id = other_project.gitlab_repo.attributes["id"]
            if project.parent is None:
                target_id = repo.attributes["id"]
                repo = other_project.gitlab_repo
        # otherwise handles PR from the same project to same project

        if target_id is not None:
            parameters["target_project_id"] = target_id

        mr = repo.mergerequests.create(parameters)
        return GitlabPullRequest(mr, target_project)

    @staticmethod
    def __get_fork(
        fork_username: str, project: "ogr_gitlab.GitlabProject"
    ) -> "ogr_gitlab.GitlabProject":
        """
        Returns forked project of a requested user. Internal method, in case the fork
        doesn't exist, raises GitlabAPIException.

        Args:
            fork_username: Username of a user that owns requested fork.
            project: Project to search forks of.

        Returns:
            Requested fork.

        Raises:
            GitlabAPIException, in case the fork doesn't exist.
        """
        forks = list(
            filter(
                lambda fork: fork.gitlab_repo.namespace["full_path"] == fork_username,
                project.get_forks(),
            )
        )
        if not forks:
            raise GitlabAPIException("Requested fork doesn't exist")
        return forks[0]

    @staticmethod
    def get(project: "ogr_gitlab.GitlabProject", pr_id: int) -> "PullRequest":
        try:
            mr = project.gitlab_repo.mergerequests.get(pr_id)
        except gitlab.GitlabGetError as ex:
            raise GitlabAPIException(f"No PR with id {pr_id} found") from ex
        return GitlabPullRequest(mr, project)

    @staticmethod
    def get_list(
        project: "ogr_gitlab.GitlabProject", status: PRStatus = PRStatus.open
    ) -> List["PullRequest"]:
        # Gitlab API has status 'opened', not 'open'
        mrs = project.gitlab_repo.mergerequests.list(
            state=status.name if status != PRStatus.open else "opened",
            order_by="updated_at",
            sort="desc",
        )
        return [GitlabPullRequest(mr, project) for mr in mrs]

    def update_info(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> "PullRequest":
        if title:
            self._raw_pr.title = title
        if description:
            self._raw_pr.description = description

        self._raw_pr.save()
        return self

    def _get_all_comments(self) -> List[PRComment]:
        return [
            GitlabPRComment(parent=self, raw_comment=raw_comment)
            for raw_comment in self._raw_pr.notes.list(sort="asc", all=True)
        ]

    def get_all_commits(self) -> List[str]:
        return [commit.id for commit in self._raw_pr.commits()]

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
        comment = self._raw_pr.notes.create({"body": body})
        return GitlabPRComment(parent=self, raw_comment=comment)

    def close(self) -> "PullRequest":
        self._raw_pr.state_event = "close"
        self._raw_pr.save()
        return self

    def merge(self) -> "PullRequest":
        self._raw_pr.merge()
        return self

    def add_label(self, *labels: str) -> None:
        self._raw_pr.labels += labels
        self._raw_pr.save()

    def get_comment(self, comment_id: int) -> PRComment:
        return GitlabPRComment(self._raw_pr.notes.get(comment_id))

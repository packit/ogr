# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from urllib.request import urlopen

from ogr.abstract import (
    CommitFlag,
    CommitStatus,
    GitProject,
    GitService,
    GitUser,
    Issue,
    IssueComment,
    PullRequest,
    Release,
)
from ogr.exceptions import OgrException
from ogr.parsing import parse_git_repo
from ogr.utils import filter_comments, search_in_comments

try:
    from functools import cached_property
except ImportError:
    from functools import lru_cache

    def cached_property(func):  # type: ignore
        return property(lru_cache()(func))


class BaseGitService(GitService):
    @cached_property
    def hostname(self) -> Optional[str]:
        parsed_url = parse_git_repo(potential_url=self.instance_url)
        return parsed_url.hostname if parsed_url else None

    def get_project_from_url(self, url: str) -> "GitProject":
        repo_url = parse_git_repo(potential_url=url)
        if not repo_url:
            raise OgrException(f"Cannot parse project url: '{url}'")
        return self.get_project(repo=repo_url.repo, namespace=repo_url.namespace)


class BaseGitProject(GitProject):
    @property
    def full_repo_name(self) -> str:
        return f"{self.namespace}/{self.repo}"


class BasePullRequest(PullRequest):
    @property
    def target_branch_head_commit(self) -> str:
        return self.target_project.get_sha_from_branch(self.target_branch)

    def get_comments(
        self,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ):
        all_comments = self._get_all_comments()
        return filter_comments(all_comments, filter_regex, reverse, author)

    def search(
        self,
        filter_regex: str,
        reverse: bool = False,
        description: bool = True,
    ):
        all_comments: list[Any] = self.get_comments(reverse=reverse)
        if description:
            description_content = self.description
            if reverse:
                all_comments.append(description_content)
            else:
                all_comments.insert(0, description_content)

        return search_in_comments(comments=all_comments, filter_regex=filter_regex)

    def get_statuses(self) -> list[CommitFlag]:
        commit = self.get_all_commits()[-1]
        return self.target_project.get_commit_statuses(commit)


class BaseGitUser(GitUser):
    pass


class BaseIssue(Issue):
    def get_comments(
        self,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> list[IssueComment]:
        all_comments: list[IssueComment] = self._get_all_comments()
        return filter_comments(all_comments, filter_regex, reverse, author)

    def can_close(self, username: str) -> bool:
        return username == self.author or username in self.project.who_can_close_issue()


class BaseCommitFlag(CommitFlag):
    @classmethod
    def _state_from_str(cls, state: str) -> CommitStatus:
        if state not in cls._states:
            raise ValueError("Invalid state given")
        return cls._states[state]

    @classmethod
    def _validate_state(cls, state: CommitStatus) -> CommitStatus:
        if state not in cls._states.values():
            raise ValueError("Invalid state given")

        return state


class BaseRelease(Release):
    def save_archive(self, filename: str) -> None:
        response = urlopen(self.tarball_url)
        data = response.read()

        with open(filename, "wb") as file:
            file.write(data)

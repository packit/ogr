# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
from collections.abc import Iterable

import github
import requests
from github.Commit import Commit as _GitCommit

from ogr.abstract.commit import CommitChanges
from ogr.exceptions import GithubAPIException, OgrNetworkError
from ogr.services import github as ogr_github
from ogr.services.base import BaseGitCommit
from ogr.services.github.pull_request import GithubPullRequest


class GithubCommit(BaseGitCommit):
    _raw_commit: _GitCommit
    _changes: "GithubCommitChanges" = None

    @property
    def sha(self) -> str:
        return self._raw_commit.sha

    @property
    def changes(self) -> "GithubCommitChanges":
        if not self._changes:
            self._changes = GithubCommitChanges(self)
        return self._changes

    def get_prs(self) -> Iterable[GithubPullRequest]:
        for pr in self._raw_commit.get_pulls():
            yield GithubPullRequest(pr, self.project)

    @staticmethod
    def get(project: "ogr_github.GithubProject", sha: str) -> "GithubCommit":
        try:
            commit = project.github_repo.get_commit(sha=sha)
        except github.UnknownObjectException as ex:
            raise GithubAPIException(f"No git commit with id {sha} found") from ex
        return GithubCommit(commit, project)


class GithubCommitChanges(CommitChanges):
    commit: "ogr_github.GithubCommit"

    @property
    def files(self) -> Iterable[str]:
        for file in self.commit._raw_commit.files:
            yield file.filename

    @property
    def patch(self) -> bytes:
        patch_url = f"{self.commit._raw_commit.html_url}.patch"
        response = requests.get(patch_url)

        if not response.ok:
            cls = OgrNetworkError if response.status_code >= 500 else GithubAPIException
            raise cls(
                f"Couldn't get patch from {patch_url} because {response.reason}.",
            )

        return response.content

    @property
    def diff_url(self) -> str:
        return f"{self.commit._raw_commit.html_url}.diff"

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
import github
from github.Commit import Commit as _GitCommit

from ogr.exceptions import GithubAPIException
from ogr.services import github as ogr_github
from ogr.services.base import BaseGitCommit
from ogr.services.github.changes import GithubCommitChanges


class GithubCommit(BaseGitCommit):
    _raw_commit: _GitCommit
    _changes: GithubCommitChanges = None

    @property
    def sha(self) -> str:
        return self._raw_commit.sha

    @property
    def changes(self) -> GithubCommitChanges:
        if not self._changes:
            self._changes = GithubCommitChanges(self)
        return self._changes

    @staticmethod
    def get(project: "ogr_github.GithubProject", sha: str) -> "GithubCommit":
        try:
            commit = project.github_repo.get_commit(sha=sha)
        except github.UnknownObjectException as ex:
            raise GithubAPIException(f"No git commit with id {sha} found") from ex
        return GithubCommit(commit, project)

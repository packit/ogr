# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
from collections.abc import Iterable

import requests

from ogr.abstract import CommitChanges, PullRequestChanges
from ogr.exceptions import GithubAPIException, OgrNetworkError
from ogr.services import github as ogr_github


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


class GithubPullRequestChanges(PullRequestChanges):
    pull_request: "ogr_github.GithubPullRequest"

    @property
    def files(self) -> Iterable[str]:
        for file in self.pull_request._raw_pr.get_files():
            yield file.filename

    @property
    def patch(self) -> bytes:
        patch_url = self.pull_request._raw_pr.patch_url
        response = requests.get(patch_url)

        if not response.ok:
            cls = OgrNetworkError if response.status_code >= 500 else GithubAPIException
            raise cls(
                f"Couldn't get patch from {patch_url} because {response.reason}.",
            )

        return response.content

    @property
    def diff_url(self) -> str:
        return f"{self.pull_request._raw_pr.html_url}.diff"

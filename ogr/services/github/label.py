# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
from typing import Union

from github.Label import Label as _GithubLabel

from ogr.abstract import Issue, IssueLabel, Label, PRLabel, PullRequest


class GithubLabel(Label):
    def __init__(
        self,
        raw_label: _GithubLabel,
        parent: Union[PullRequest, Issue],
    ) -> None:
        super().__init__(parent)
        self._raw_label = raw_label

    def __str__(self) -> str:
        return f'GithubLabel(name="{self.name}")'

    @property
    def name(self):
        return self._raw_label.name


class GithubPRLabel(GithubLabel, PRLabel):
    pass


class GithubIssueLabel(GithubLabel, IssueLabel):
    pass

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
from typing import Union

from ogr.abstract import Issue, IssueLabel, Label, PRLabel, PullRequest


class PagureLabel(Label):
    def __init__(self, name: str, parent: Union[PullRequest, Issue]) -> None:
        super().__init__(parent)
        self._name = name

    def __str__(self) -> str:
        return f'PagureLabel(name="{self.name}")'

    @property
    def name(self):
        return self._name


class PagurePRLabel(PagureLabel, PRLabel):
    pass


class PagureIssueLabel(PagureLabel, IssueLabel):
    pass

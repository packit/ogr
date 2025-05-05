# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT
from typing import Union

from pyforgejo.types import Label as PyforgejoLabel

from ogr.abstract import Issue, IssueLabel, Label, PRLabel, PullRequest


class ForgejoLabel(Label):
    def __init__(
        self,
        raw_label: PyforgejoLabel,
        parent: Union[PullRequest, Issue],
    ) -> None:
        super().__init__(parent)
        self._raw_label = raw_label

    def __str__(self) -> str:
        return f'ForgejoLabel(name="{self.name}")'

    @property
    def name(self):
        return self._raw_label.name


class ForgejoPRLabel(ForgejoLabel, PRLabel):
    pass


class ForgejoIssueLabel(ForgejoLabel, IssueLabel):
    pass

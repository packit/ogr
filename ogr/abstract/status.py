# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from enum import Enum, IntEnum


class IssueStatus(IntEnum):
    """Enumeration for issue statuses."""

    open = 1
    closed = 2
    all = 3


class PRStatus(IntEnum):
    """Enumeration that represents statuses of pull requests."""

    open = 1
    closed = 2
    merged = 3
    all = 4


class CommitStatus(Enum):
    """Enumeration that represents possible state of commit statuses."""

    pending = 1
    success = 2
    failure = 3
    error = 4
    canceled = 5
    running = 6
    warning = 7


class MergeCommitStatus(Enum):
    """Enumeration that represents possible states of merge states of PR/MR."""

    can_be_merged = 1
    cannot_be_merged = 2
    unchecked = 3
    checking = 4
    cannot_be_merged_recheck = 5

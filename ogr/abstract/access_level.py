# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from enum import IntEnum


class AccessLevel(IntEnum):
    """
    Enumeration representing an access level to the repository.

    | Value from enumeration | GitHub   | GitLab                  | Pagure |
    | ---------------------- | -------- | ----------------------- | ------ |
    | `AccessLevel.pull`     | pull     | guest                   | ticket |
    | `AccessLevel.triage`   | triage   | reporter                | ticket |
    | `AccessLevel.push`     | push     | developer               | commit |
    | `AccessLevel.admin`    | admin    | maintainer              | commit |
    | `AccessLevel.maintain` | maintain | owner (only for groups) | admin  |
    """

    pull = 1
    triage = 2
    push = 3
    admin = 4
    maintain = 5

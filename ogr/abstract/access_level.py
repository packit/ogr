# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from enum import IntEnum


class AccessLevel(IntEnum):
    """
    Enumeration representing an access level to the repository.

    | Value from enumeration | GitHub   | GitLab                  | Pagure | Forgejo |
    | ---------------------- | -------- | ----------------------- | ------ | ------- |
    | `AccessLevel.pull`     | pull     | guest                   | ticket | read    |
    | `AccessLevel.triage`   | triage   | reporter                | ticket | read    |
    | `AccessLevel.push`     | push     | developer               | commit | write   |
    | `AccessLevel.admin`    | admin    | maintainer              | commit | admin   |
    | `AccessLevel.maintain` | maintain | owner (only for groups) | admin  | owner   |

    Note: ``has_permission()`` uses conservative fallbacks for forges
    that lack a triage equivalent — a triage check requires commit
    on Pagure and write on Forgejo, not ticket/read.
    """

    pull = 1
    triage = 2
    push = 3
    admin = 4
    maintain = 5

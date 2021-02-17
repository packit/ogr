# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from deprecated import deprecated


def deprecate_and_set_removal(since, remove_in, message):
    return deprecated(
        version=since, reason=f"will be removed in {remove_in}: {message}"
    )

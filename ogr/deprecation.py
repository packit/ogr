# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from deprecated import deprecated


def deprecate_and_set_removal(since: str, remove_in: str, message: str):
    """
    Decorator for deprecating functions in ogr.

    Args:
        since: Indicates a version since which is attribute deprecated.
        remove_in: Indicates a version in which the attribute will be removed.
        message: Message to be included with deprecation.

    Returns:
        Decorator.
    """
    return deprecated(
        version=since,
        reason=f"will be removed in {remove_in}: {message}",
    )

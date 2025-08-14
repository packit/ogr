# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from ogr.abstract.abstract_class import OgrAbstractClass


class GitTag(OgrAbstractClass):
    """
    Class representing a git tag.

    Attributes:
        name (str): Name of the tag.
        commit_sha (str): Commit hash of the tag.
    """

    def __init__(self, name: str, commit_sha: str) -> None:
        self.name = name
        self.commit_sha = commit_sha

    def __str__(self) -> str:
        return f"GitTag(name={self.name}, commit_sha={self.commit_sha})"

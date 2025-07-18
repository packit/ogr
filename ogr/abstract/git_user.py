# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from collections.abc import Iterable, Sequence
from typing import Union

from ogr.abstract.abstract_class import OgrAbstractClass

import typing

if typing.TYPE_CHECKING:
    from .git_project import GitProject
    from .git_service import GitService


class GitUser(OgrAbstractClass):
    """
    Represents currently authenticated user through service.
    """

    def __init__(self, service: GitService) -> None:
        self.service = service

    def get_username(self) -> str:
        """
        Returns:
            Login of the user.
        """
        raise NotImplementedError()

    def get_email(self) -> str:
        """
        Returns:
            Email of the user.
        """
        raise NotImplementedError()

    def get_projects(self) -> Union[Sequence["GitProject"], Iterable["GitProject"]]:
        """
        Returns:
            Sequence of projects in user's namespace.
        """
        raise NotImplementedError()

    def get_forks(self) -> Union[Sequence["GitProject"], Iterable["GitProject"]]:
        """
        Returns:
            Sequence of forks in user's namespace.
        """
        raise NotImplementedError()
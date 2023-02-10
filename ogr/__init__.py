# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
Module providing one api for multiple git services (github/gitlab/pagure)
"""

from importlib.metadata import PackageNotFoundError, distribution

from ogr.factory import (
    get_project,
    get_service_class,
    get_service_class_or_none,
    get_instances_from_dict,
)
from ogr.services.github import GithubService
from ogr.services.gitlab import GitlabService
from ogr.services.pagure import PagureService
from ogr.abstract import AuthMethod

try:
    __version__ = distribution(__name__).version
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = [
    GithubService.__name__,
    PagureService.__name__,
    GitlabService.__name__,
    AuthMethod.__name__,
    get_project.__name__,
    get_service_class.__name__,
    get_service_class_or_none.__name__,
    get_instances_from_dict.__name__,
]

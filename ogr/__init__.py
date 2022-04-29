# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
Module providing one api for multiple git services (github/gitlab/pagure)
"""

from ogr.factory import (
    get_project,
    get_service_class,
    get_service_class_or_none,
    get_instances_from_dict,
)
from ogr.services.github import GithubService
from ogr.services.gitlab import GitlabService
from ogr.services.pagure import PagureService

try:
    from importlib.metadata import PackageNotFoundError, distribution
except ImportError:
    from importlib_metadata import PackageNotFoundError  # type: ignore
    from importlib_metadata import distribution  # type: ignore

try:
    __version__ = distribution(__name__).version
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = [
    GithubService.__name__,
    PagureService.__name__,
    GitlabService.__name__,
    get_project.__name__,
    get_service_class.__name__,
    get_service_class_or_none.__name__,
    get_instances_from_dict.__name__,
]

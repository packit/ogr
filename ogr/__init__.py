# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
Module providing one api for multiple git services (github/gitlab/pagure)
"""

from pkg_resources import get_distribution, DistributionNotFound

from ogr.factory import (
    get_project,
    get_service_class,
    get_service_class_or_none,
    get_instances_from_dict,
)

from ogr.services.github import *
from ogr.services.gitlab import *
from ogr.services.pagure import *

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

__all__ = [
    #services.github
    GithubService.__name__,
    GithubCheckRun.__name__,
    GithubPullRequest.__name__,
    GithubIssueComment.__name__,
    GithubPRComment.__name__,
    GithubIssue.__name__,
    GithubRelease.__name__,
    GithubUser.__name__,
    GithubProject.__name__,

    #services.gitlab
    GitlabService.__name__,
    GitlabIssue.__name__,
    GitlabPullRequest.__name__,
    GitlabIssueComment.__name__,
    GitlabPRComment.__name__,
    GitlabRelease.__name__,
    GitlabUser.__name__,
    GitlabProject.__name__,

    PagureService.__name__,
    PagurePullRequest.__name__,
    PagureIssueComment.__name__,
    PagurePRComment.__name__,
    PagureIssue.__name__,
    PagureRelease.__name__,
    PagureUser.__name__,
    PagureProject.__name__,

    get_project.__name__,
    get_service_class.__name__,
    get_service_class_or_none.__name__,
    get_instances_from_dict.__name__,
]


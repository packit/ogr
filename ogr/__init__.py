# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Module for:
- simplifying the python work with git
- introduce one api for multiple git services (github/gitlab/pagure)
"""
import os

from pkg_resources import get_distribution, DistributionNotFound

from ogr.factory import get_project, get_service_class

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

mock_env = os.getenv("RECORD_REQUESTS")
if mock_env:
    from ogr.services.mock.github import (
        BetterGithubIntegrationMock as BetterGithubIntegration,
    )

    import ogr.services.mock.github_import_tweaks  # noqa: F401
    from ogr.services.github import GithubService
    from ogr.services.mock import PagureService


else:
    from ogr.services.github_tweak import BetterGithubIntegration
    from ogr.services.github import GithubService
    from ogr.services.pagure import PagureService

__all__ = [
    GithubService.__name__,
    PagureService.__name__,
    get_project.__name__,
    get_service_class.__name__,
    BetterGithubIntegration.__name__,
]

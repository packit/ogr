"""
Module for:
- simplifying the python work with git
- intruduce one api for multiple git services (github/gitlab/pagure)
"""

from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

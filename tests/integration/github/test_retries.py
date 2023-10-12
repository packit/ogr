# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest
from flexmock import flexmock
from github import Github
from github.GithubException import BadCredentialsException
from urllib3.connectionpool import HTTPSConnectionPool

from ogr import GithubService


@pytest.mark.skip(reason="Will fail until flexmock is fixed")
@pytest.mark.parametrize("max_retries", [0, 2])
def test_bad_credentials(max_retries):
    flexmock(HTTPSConnectionPool).should_call("urlopen").times(max_retries + 1)

    flexmock(Github).should_call("get_repo").and_raise(
        BadCredentialsException,
        401,
        {
            "message": "Bad credentials",
            "documentation_url": "https://docs.github.com/rest",
        },
    )

    service = GithubService(token="invalid_token", max_retries=max_retries)
    project = service.get_project(namespace="mmuzila", repo="playground")
    _ = project.github_repo

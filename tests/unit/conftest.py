# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest
from flexmock import flexmock

from ogr import PagureService


# mocks API calls to Pagure dist-git made to determine whether dist-git
# is still hosted on Pagure and returns the status code expected after
# the migration of dist-git to Forgejo
@pytest.fixture(autouse=True)
def setup_api_request_mock():
    response = flexmock(status_code=404)
    flexmock(PagureService).should_receive("get_raw_request").with_args(
        url="https://src.fedoraproject.org/api/0/version",
        timeout=5,
    ).and_return(
        response,
    )
    flexmock(PagureService).should_receive("get_raw_request").with_args(
        url="https://src.stg.fedoraproject.org/api/0/version",
        timeout=5,
    ).and_return(
        response,
    )

    return

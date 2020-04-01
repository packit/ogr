import pytest
from flexmock import flexmock

from ogr.services.pagure import PagureProject


@pytest.fixture
def mock_pull_request():
    def mock_pull_request_factory(id=42):
        mock = flexmock(id=id)
        return mock

    return mock_pull_request_factory


@pytest.fixture
def mock_github_repo(mock_pull_request):
    def mock_github_repo_factory():
        mock = flexmock(create_pull=mock_pull_request(42))
        return mock

    return mock_github_repo_factory


@pytest.fixture
def pagure_project(mock_github_repo):
    mock = flexmock(spec=PagureProject)
    return mock


@pytest.fixture
def mock_pagure_repo(mock_pull_request):
    def mock_pagure_repo_factory():
        mock = flexmock(create_pull=mock_pull_request(42))
        return mock

    return mock_pagure_repo_factory


@pytest.fixture
def data_pagure_raw_pr():
    """
    Fixtures generates PagurePullRequest._raw_pr value(s).
    :return: _raw_pr factory function

    """

    def data_pagure_raw_pr_factory(commit_stop: str = "123456abcd"):
        return {
            "commit_stop": commit_stop,
        }

    return data_pagure_raw_pr_factory

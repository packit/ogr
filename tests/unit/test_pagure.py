import pytest
from flexmock import flexmock

from ogr.services.pagure import PagureProject, PagurePullRequest


@pytest.fixture
def pagure_project(mock_github_repo):
    pagure_project = PagureProject(
        repo="test_repo", service="test_service", namespace="test_namespace"
    )
    parent_pagure_project = PagureProject(
        repo="test_parent_repo",
        service="test_service",
        namespace="test_parent_namespace",
    )
    flexmock(pagure_project)
    flexmock(parent_pagure_project)
    flexmock(PagurePullRequest)

    # pagure_project.should_receive("pagure_repo").and_return(mock_pagure_repo())
    # parent_pagure_project.should_receive("pagure_repo").and_return(mock_pagure_repo())
    # pagure_project.should_receive("parent").and_return(parent_pagure_project)
    return pagure_project


class TestPullRequest:
    def test_latest_commit(self, data_pagure_raw_pr):
        pagure_pullreqest = PagurePullRequest(
            raw_pr=data_pagure_raw_pr(commit_stop="1a2b3c"), project=None
        )

        assert pagure_pullreqest.head_commit == "1a2b3c"

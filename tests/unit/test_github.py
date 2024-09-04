# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional
from unittest import TestCase

import pytest
from flexmock import flexmock

from ogr import GithubService
from ogr.abstract import AuthMethod
from ogr.exceptions import GithubAPIException
from ogr.services.github.auth_providers.token import TokenAuthentication
from ogr.services.github.auth_providers.tokman import Tokman
from ogr.services.github.check_run import (
    GithubCheckRunOutput,
    create_github_check_run_output,
)
from ogr.services.github.project import GithubProject
from ogr.services.github.pull_request import GithubPullRequest


@pytest.fixture
def github_project(mock_github_repo):
    github_project = GithubProject(
        repo="test_repo",
        service="test_service",
        namespace="fork_username",
    )
    parent_github_project = GithubProject(
        repo="test_parent_repo",
        service="test_service",
        namespace="test_parent_namespace",
    )
    flexmock(github_project)
    flexmock(parent_github_project)
    flexmock(GithubPullRequest)

    github_project.should_receive("github_repo").and_return(mock_github_repo())
    parent_github_project.should_receive("github_repo").and_return(mock_github_repo())
    github_project.should_receive("parent").and_return(parent_github_project)
    return github_project


@pytest.fixture
def mock_pull_request():
    def mock_pull_request_factory(id):
        return flexmock(id=id)

    return mock_pull_request_factory


@pytest.fixture
def mock_github_repo(mock_pull_request):
    def mock_github_repo_factory():
        return flexmock(create_pull=mock_pull_request(42))

    return mock_github_repo_factory


class TestGithubProject:
    @pytest.mark.parametrize(
        "fork_username",
        [
            pytest.param("fork_username", id="fork_username_set"),
            pytest.param(None, id="fork_username_None"),
        ],
    )
    def test_pr_create_is_not_fork(self, github_project, fork_username):
        github_project.should_receive("is_fork").and_return(False)
        GithubPullRequest.should_receive("__init__").and_return()

        head = ":".join(filter(None, [fork_username, "master"]))

        github_project.github_repo.should_call("create_pull").with_args(
            title="test_title",
            body="test_content",
            base="master",
            head=head,
        )
        github_project.parent.github_repo.should_call("create_pull").never()
        github_project.github_repo.should_call("create_pull").once()

        github_project.create_pr(
            title="test_title",
            body="test_content",
            target_branch="master",
            source_branch="master",
            fork_username=fork_username,
        )

    @pytest.mark.parametrize(
        "fork_username",
        [pytest.param("fork_username", id="fork_username_set")],
    )
    def test_pr_create_is_fork(self, github_project, fork_username):
        github_project.should_receive("is_fork").and_return(True)
        GithubPullRequest.should_receive("__init__").and_return()

        github_project.parent.github_repo.should_call("create_pull").with_args(
            title="test_title",
            body="test_content",
            base="master",
            head=f"{github_project}:master",
            fork_username=fork_username,
        )
        github_project.parent.github_repo.should_call("create_pull").never()
        github_project.github_repo.should_call("create_pull").once()

        github_project.create_pr(
            title="test_title",
            body="test_content",
            target_branch="master",
            source_branch="master",
            fork_username=fork_username,
        )


class TestGitHubService(TestCase):
    def test_hostname(self):
        assert GithubService().hostname == "github.com"


@pytest.mark.parametrize(
    ("title", "summary", "text", "expected"),
    [
        (
            "test",
            "test summary",
            None,
            {
                "title": "test",
                "summary": "test summary",
            },
        ),
        (
            "bigger output",
            "no summary",
            "# Random title\n\n- [ ] TODO list\n---\n_italics_",
            {
                "title": "bigger output",
                "summary": "no summary",
                "text": "# Random title\n\n- [ ] TODO list\n---\n_italics_",
            },
        ),
    ],
)
def test_create_github_check_run_output(
    title: str,
    summary: str,
    text: Optional[str],
    expected: GithubCheckRunOutput,
) -> None:
    assert create_github_check_run_output(title, summary, text) == expected


@pytest.fixture
def github_service_with_multiple_auth_methods():
    return GithubService(
        token="abcdef",
        github_app_id="123",
        github_app_private_key="id_rsa",
        github_app_private_key_path="/path",
        tokman_instance_url="http://tokman:8080",
        github_authentication=None,
    )


def test_multiple_auth_methods_default_is_tokman(
    github_service_with_multiple_auth_methods,
):
    service = github_service_with_multiple_auth_methods
    assert isinstance(service.authentication, Tokman)


def test_set_reset_customized_auth_method(github_service_with_multiple_auth_methods):
    service = github_service_with_multiple_auth_methods
    assert isinstance(service.authentication, Tokman)
    service.set_auth_method(AuthMethod.token)
    assert isinstance(service.authentication, TokenAuthentication)
    service.reset_auth_method()
    assert isinstance(service.authentication, Tokman)


@pytest.fixture
def github_service_with_one_auth_method():
    return GithubService(
        tokman_instance_url="http://tokman:8080",
        github_authentication=None,
    )


def test_no_multiple_auth_methods_default_is_tokman(
    github_service_with_one_auth_method,
):
    service = github_service_with_one_auth_method
    assert isinstance(service.authentication, Tokman)


def test_no_set_reset_customized_auth_method(github_service_with_one_auth_method):
    service = github_service_with_one_auth_method
    assert isinstance(service.authentication, Tokman)
    with pytest.raises(GithubAPIException):
        service.set_auth_method(AuthMethod.github_app)
    assert isinstance(service.authentication, Tokman)

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest
from flexmock import flexmock
from pydantic import ValidationError
from pyforgejo.core.api_error import ApiError
from pyforgejo.core.pydantic_utilities import parse_obj_as
from pyforgejo.types import CommitStatus as PyforgejoCommitStatus
from pyforgejo.types import ContentsResponse

from ogr.abstract import CommitStatus
from ogr.exceptions import ForgejoAPIException, GitForgeInternalError
from ogr.services.forgejo import ForgejoProject, ForgejoService
from ogr.services.forgejo.pull_request import ForgejoPullRequest

HEAD_SHA = "d490ec67dd98f69dfdc1732b98bb3189f0e0aace"


def test_pr_get_statuses():
    service = ForgejoService(instance_url="https://forgejo.example.com")
    project = ForgejoProject(repo="repo", service=service, namespace="namespace")
    raw_pr = flexmock(head=flexmock(sha=HEAD_SHA))
    pr = ForgejoPullRequest(raw_pr=raw_pr, project=project)

    raw_status = PyforgejoCommitStatus(
        id=1,
        status="success",
        context="ci / test",
        description="Successful in 1m",
        target_url="https://forgejo.example.com/namespace/repo/actions/runs/1",
    )
    repository_api = flexmock()
    repository_api.should_receive("repo_list_statuses").with_args(
        owner="namespace",
        repo="repo",
        sha=HEAD_SHA,
        page=1,
    ).and_return([raw_status]).once()
    repository_api.should_receive("repo_list_statuses").with_args(
        owner="namespace",
        repo="repo",
        sha=HEAD_SHA,
        page=2,
    ).and_return([]).once()
    flexmock(ForgejoProject).should_receive("api").and_return(repository_api)

    statuses = list(pr.get_statuses())

    assert len(statuses) == 1
    assert statuses[0].commit == HEAD_SHA
    assert statuses[0].state == CommitStatus.success
    assert statuses[0].context == "ci / test"
    assert statuses[0].comment == "Successful in 1m"


def _listing_validation_error(listing: list[dict]) -> ValidationError:
    # what pyforgejo 2.0.0 raises for a directory: it validates the list
    # returned by the contents endpoint as a single ‹ContentsResponse›
    try:
        parse_obj_as(ContentsResponse, listing)
    except ValidationError as ex:
        return ex
    raise AssertionError("a list must not validate as ContentsResponse")


def test_get_files_pyforgejo_2_0_0_directory_listing():
    service = ForgejoService(instance_url="https://forgejo.example.com")
    project = ForgejoProject(repo="repo", service=service, namespace="namespace")

    root = [
        {"name": "README.md", "path": "README.md", "type": "file"},
        {"name": "docs", "path": "docs", "type": "dir"},
    ]
    docs = [{"name": "index.md", "path": "docs/index.md", "type": "file"}]
    repository_api = flexmock()
    repository_api.should_receive("repo_get_contents").with_args(
        owner="namespace",
        repo="repo",
        filepath=".",
        ref="main",
    ).and_raise(_listing_validation_error(root)).once()
    repository_api.should_receive("repo_get_contents").with_args(
        owner="namespace",
        repo="repo",
        filepath="docs",
        ref="main",
    ).and_raise(_listing_validation_error(docs)).once()
    flexmock(ForgejoProject).should_receive("api").and_return(repository_api)

    assert sorted(project.get_files(ref="main")) == ["README.md", "docs/index.md"]


def _api_error(status_code: int, message: str) -> ApiError:
    error = ApiError(
        status_code=status_code,
        body={"message": message, "url": "https://forgejo.example.com/api/swagger"},
    )
    # pyforgejo 2.0.1 and later print the headers in str(); 2.0.0 has none
    error.headers = {"set-cookie": "i_like_forgejo=secret"}
    return error


def _project() -> ForgejoProject:
    service = ForgejoService(instance_url="https://forgejo.example.com")
    return ForgejoProject(repo="repo", service=service, namespace="namespace")


def test_api_error_is_wrapped_without_headers():
    project = _project()
    repository_api = flexmock()
    repository_api.should_receive("repo_delete").and_raise(
        _api_error(403, "token does not have required scope"),
    ).once()
    flexmock(ForgejoProject).should_receive("api").and_return(repository_api)

    with pytest.raises(ForgejoAPIException) as exc_info:
        project.delete()

    assert exc_info.value.response_code == 403
    assert exc_info.value.forgejo_message == "token does not have required scope"
    assert str(exc_info.value) == "403 token does not have required scope"
    assert "secret" not in str(exc_info.value)


def test_api_error_in_pagination_is_wrapped():
    project = _project()
    repository_api = flexmock()
    repository_api.should_receive("repo_list_pull_requests").and_raise(
        _api_error(404, "repository does not exist"),
    ).once()
    flexmock(ForgejoProject).should_receive("api").and_return(repository_api)

    prs = project.get_pr_list()
    with pytest.raises(ForgejoAPIException) as exc_info:
        list(prs)

    assert exc_info.value.response_code == 404
    assert exc_info.value.forgejo_message == "repository does not exist"
    assert "secret" not in str(exc_info.value)


def test_server_error_in_pagination_is_internal_error():
    project = _project()
    raw_pr = flexmock(head=flexmock(sha=HEAD_SHA))
    pr = ForgejoPullRequest(raw_pr=raw_pr, project=project)
    repository_api = flexmock()
    repository_api.should_receive("repo_list_statuses").and_raise(
        _api_error(502, "bad gateway"),
    ).once()
    flexmock(ForgejoProject).should_receive("api").and_return(repository_api)

    with pytest.raises(GitForgeInternalError):
        list(pr.get_statuses())


def test_forgejo_message_without_json_body():
    error = ApiError(status_code=500, body=None)
    wrapped = ForgejoAPIException(ForgejoAPIException.describe(error))
    wrapped.__cause__ = error

    assert str(wrapped) == "500"
    assert wrapped.forgejo_message is None

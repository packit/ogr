# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from flexmock import flexmock
from pydantic import ValidationError
from pyforgejo.core.pydantic_utilities import parse_obj_as
from pyforgejo.types import CommitStatus as PyforgejoCommitStatus
from pyforgejo.types import ContentsResponse

from ogr.abstract import CommitStatus
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

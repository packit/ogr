# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime

import pytest

from ogr.abstract import CommitFlag, CommitStatus
from ogr.services.forgejo.commit_flag import ForgejoCommitFlag


def fake_get_commit_statuses(self, owner, repo, commit):
    return [
        {
            "commit": commit,
            "state": "success",
            "context": "CI",
            "comment": "All tests passed",
            "id": "123",
            "url": f"http://dummy-forgejo/commit/{commit}/status",
            "created": datetime.datetime.strptime(
                "2023-01-01T12:00:00Z",
                "%Y-%m-%dT%H:%M:%SZ",
            ),
            "updated": datetime.datetime.strptime(
                "2023-01-01T12:30:00Z",
                "%Y-%m-%dT%H:%M:%SZ",
            ),
        },
    ]


def fake_set_commit_status(
    self,
    owner,
    repo,
    commit,
    state,
    target_url,
    description,
    context,
):
    return {
        "commit": commit,
        "state": state,
        "context": context,
        "comment": description,
        "id": "456",
        "url": f"http://dummy-forgejo/commit/{commit}/status",
        "created": datetime.datetime.strptime(
            "2023-02-01T12:00:00Z",
            "%Y-%m-%dT%H:%M:%SZ",
        ),
        "updated": datetime.datetime.strptime(
            "2023-02-01T12:30:00Z",
            "%Y-%m-%dT%H:%M:%SZ",
        ),
    }


class FakePyforgejoApi:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.token = token

    def get_commit_statuses(self, owner, repo, commit):
        return fake_get_commit_statuses(self, owner, repo, commit)

    def set_commit_status(
        self,
        owner,
        repo,
        commit,
        state,
        target_url,
        description,
        context,
    ):
        return fake_set_commit_status(
            self,
            owner,
            repo,
            commit,
            state,
            target_url,
            description,
            context,
        )


class MockProject:
    forge_api_url = "http://dummy-forgejo/api/v1"
    owner = "dummy_owner"
    repo = "dummy_repo"
    token = "dummy_token"

    def get_auth_header(self) -> dict[str, str]:
        return {"Authorization": "Bearer dummy_token"}


@pytest.fixture(autouse=True)
def patch_pyforgejo_api(monkeypatch):
    monkeypatch.setattr(
        "ogr.services.forgejo.commit_flag.PyforgejoApi",
        FakePyforgejoApi,
    )


def test_get_commit_flag_integration():
    project = MockProject()
    commit = "abcdef123456"

    flags: list[CommitFlag] = ForgejoCommitFlag.get(project, commit)

    assert len(flags) == 1
    flag = flags[0]
    assert flag.commit == commit
    assert flag.state == CommitStatus.success
    assert flag.context == "CI"
    assert flag.comment == "All tests passed"
    assert flag.uid == "123"

    expected_created = datetime.datetime.strptime(
        "2023-01-01T12:00:00Z",
        "%Y-%m-%dT%H:%M:%SZ",
    )
    expected_updated = datetime.datetime.strptime(
        "2023-01-01T12:30:00Z",
        "%Y-%m-%dT%H:%M:%SZ",
    )
    assert flag.created == expected_created
    assert flag.edited == expected_updated


def test_set_commit_flag_integration():
    project = MockProject()
    commit = "abcdef123456"

    flag = ForgejoCommitFlag.set(
        project=project,
        commit=commit,
        state=CommitStatus.success,
        target_url="http://dummy-target",
        description="Build succeeded",
        context="CI",
    )

    assert flag.commit == commit
    assert flag.state == CommitStatus.success
    assert flag.context == "CI"
    assert flag.comment == "Build succeeded"
    assert flag.uid == "456"

    expected_created = datetime.datetime.strptime(
        "2023-02-01T12:00:00Z",
        "%Y-%m-%dT%H:%M:%SZ",
    )
    expected_updated = datetime.datetime.strptime(
        "2023-02-01T12:30:00Z",
        "%Y-%m-%dT%H:%M:%SZ",
    )
    assert flag.created == expected_created
    assert flag.edited == expected_updated

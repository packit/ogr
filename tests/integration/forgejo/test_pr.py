# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from unittest.mock import patch

import pytest

from ogr.abstract import PRStatus
from ogr.services.forgejo.pr import ForgejoPullRequest


class DummyPRLabel:
    def __init__(self, label_data):
        self._label_data = label_data

    @property
    def name(self) -> str:
        if isinstance(self._label_data, dict):
            return self._label_data.get("name", "")
        return str(self._label_data)


@pytest.fixture(autouse=True)
def patch_prlabel(monkeypatch):
    # Import the module where PRLabel is defined
    import ogr.services.forgejo.pr as pr_module

    monkeypatch.setattr(pr_module, "PRLabel", DummyPRLabel)


@pytest.fixture
def mock_pr_data():
    return {
        "id": 123,
        "title": "Fix bug in feature X",
        "body": "This PR fixes a critical bug.",
        "state": "open",
        "status": "open",
        "user": {"login": "contributor"},
        "base": {"ref": "main"},
        "head": {"ref": "feature-branch", "sha": "abc123"},
        "created_at": "2024-03-23T12:00:00Z",
        "html_url": "https://forgejo.example.com/org/repo/pulls/123",
        "labels": [{"name": "bug"}],
        "patch_url": "https://forgejo.example.com/org/repo/pulls/123.patch",
        "diff_url": "https://forgejo.example.com/org/repo/pulls/123.diff",
    }


def test_pull_request_properties(mock_pr_data):
    pr = ForgejoPullRequest(mock_pr_data, project=None)

    assert pr.id == 123
    assert pr.title == "Fix bug in feature X"
    assert pr.description == "This PR fixes a critical bug."
    assert pr.status == PRStatus.open
    assert pr.author == "contributor"
    assert pr.source_branch == "feature-branch"
    assert pr.target_branch == "main"
    assert pr.url == "https://forgejo.example.com/org/repo/pulls/123"
    assert pr.diff_url == "https://forgejo.example.com/org/repo/pulls/123.diff"
    assert pr.patch == b""
    assert isinstance(pr.created, datetime.datetime)
    assert len(pr.labels) == 1
    assert pr.labels[0].name == "bug"


@patch("ogr.services.forgejo.pr.ForgejoPullRequest.create")
def test_create_pull_request(mock_create, mock_pr_data):
    mock_create.return_value = ForgejoPullRequest(mock_pr_data, project=None)
    pr = ForgejoPullRequest.create(
        project=None,
        title="Fix bug in feature X",
        body="This PR fixes a critical bug.",
        target_branch="main",
        source_branch="feature-branch",
    )
    assert pr.id == 123
    assert pr.title == "Fix bug in feature X"


@patch("ogr.services.forgejo.pr.ForgejoPullRequest.get_list")
def test_get_pull_requests_list(mock_get_list, mock_pr_data):
    mock_get_list.return_value = [ForgejoPullRequest(mock_pr_data, project=None)]
    pr_list = ForgejoPullRequest.get_list(project=None, status=PRStatus.open)
    assert len(pr_list) == 1
    assert pr_list[0].id == 123

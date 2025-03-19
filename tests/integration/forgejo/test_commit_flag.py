# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import responses
import pytest
from typing import Any, Dict, List, Optional
import requests

from ogr.abstract import CommitStatus, CommitFlag
from ogr.services.forgejo.commit_flag import ForgejoCommitFlag

class MockProject:
    forge_api_url = "http://dummy-forgejo/api/v1"
    owner = "dummy_owner"
    repo = "dummy_repo"

    def get_auth_header(self) -> Dict[str, str]:
        return {"Authorization": "Bearer dummy_token"}

@responses.activate
def test_get_commit_flag_integration():
    project = MockProject()
    commit = "abcdef123456"
    url = f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/commits/{commit}/statuses"
    
    # Dummy response data simulating Forgejo API output.
    dummy_response = [{
        "commit": commit,
        "state": "success",
        "context": "CI",
        "comment": "All tests passed",
        "id": "123",
        "url": "http://dummy-forgejo/commit/abcdef123456/status",
        "created": "2023-01-01T12:00:00Z",
        "updated": "2023-01-01T12:30:00Z"
    }]
    responses.add(responses.GET, url, json=dummy_response, status=200)
    
    # Call the method under test.
    flags: List[CommitFlag] = ForgejoCommitFlag.get(project, commit)
    
    # Assertions using CommitStatus from packit.ogr.abstract.
    assert len(flags) == 1
    flag = flags[0]
    assert flag.commit == commit
    assert flag.state == CommitStatus.success
    assert flag.context == "CI"
    assert flag.comment == "All tests passed"
    assert flag.uid == "123"
    
    expected_created = datetime.datetime.strptime("2023-01-01T12:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    expected_updated = datetime.datetime.strptime("2023-01-01T12:30:00Z", "%Y-%m-%dT%H:%M:%SZ")
    assert flag.created == expected_created
    assert flag.edited == expected_updated

@responses.activate
def test_set_commit_flag_integration():
    project = MockProject()
    commit = "abcdef123456"
    url = f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/commits/{commit}/statuses"
    
    # Dummy response for setting a commit status.
    dummy_response = {
        "commit": commit,
        "state": "success",
        "context": "CI",
        "comment": "Build succeeded",
        "id": "456",
        "url": "http://dummy-forgejo/commit/abcdef123456/status",
        "created": "2023-02-01T12:00:00Z",
        "updated": "2023-02-01T12:30:00Z"
    }
    responses.add(responses.POST, url, json=dummy_response, status=200)
    
    # Call the set method to create a new commit flag.
    flag = ForgejoCommitFlag.set(
        project=project,
        commit=commit,
        state=CommitStatus.success,
        target_url="http://dummy-target",
        description="Build succeeded",
        context="CI"
    )
    
    # Assertions to verify correct mapping using CommitStatus.
    assert flag.commit == commit
    assert flag.state == CommitStatus.success
    assert flag.context == "CI"
    assert flag.comment == "Build succeeded"
    assert flag.uid == "456"
    
    expected_created = datetime.datetime.strptime("2023-02-01T12:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    expected_updated = datetime.datetime.strptime("2023-02-01T12:30:00Z", "%Y-%m-%dT%H:%M:%SZ")
    assert flag.created == expected_created
    assert flag.edited == expected_updated

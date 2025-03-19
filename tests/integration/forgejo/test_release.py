# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime

import pytest

from ogr.services.forgejo.release import ForgejoRelease


class FakeForgejoAPI:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.token = token

    def get_releases(self, owner, repo, params=None):
        # Use the "tag" parameter to simulate a release.
        tag = params.get("tag") if params and "tag" in params else "v1.0.0"
        return {
            "name": tag,
            "description": "Initial release",
            "tag_name": tag,
            "html_url": f"http://dummy-forgejo/release/{tag}",
            "created_at": "2023-01-01T12:00:00Z",
            "tarball_url": f"http://dummy-forgejo/release/{tag}/tarball",
            "commit_sha": "abcdef123456",
        }

    def create_release(self, owner, repo, payload):
        tag = payload.get("tag_name")
        return {
            "name": payload.get("name"),
            "description": payload.get("body"),
            "tag_name": tag,
            "html_url": f"http://dummy-forgejo/release/{tag}",
            "created_at": "2023-02-01T12:00:00Z",
            "tarball_url": f"http://dummy-forgejo/release/{tag}/tarball",
            "commit_sha": "abcdef7890",
        }


class MockProject:
    forge_api_url = "http://dummy-forgejo/api/v1"
    owner = "dummy_owner"
    repo = "dummy_repo"
    token = "dummy_token"

    def get_auth_header(self) -> dict[str, str]:
        return {"Authorization": "Bearer dummy_token"}


@pytest.fixture(autouse=True)
def patch_pyforgejo_api(monkeypatch):
    monkeypatch.setattr("ogr.services.forgejo.release.PyforgejoApi", FakeForgejoAPI)


def test_get_release_integration():
    project = MockProject()
    tag_name = "v1.0.0"
    release = ForgejoRelease.get(project, tag_name=tag_name)

    # Assertions on the properties.
    assert release.title == "v1.0.0"
    assert release.body == "Initial release"
    assert release.tag_name == "v1.0.0"
    assert release.url == f"http://dummy-forgejo/release/{tag_name}"
    expected_created = datetime.datetime.strptime(
        "2023-01-01T12:00:00Z",
        "%Y-%m-%dT%H:%M:%SZ",
    )
    assert release.created_at == expected_created
    assert release.tarball_url == f"http://dummy-forgejo/release/{tag_name}/tarball"

    # Verify the git_tag property returns a ForgejoGitTag with correct values.
    git_tag = release.git_tag
    expected_git_tag_str = f"GitTag(name={tag_name}, commit_sha=abcdef123456)"
    assert str(git_tag) == expected_git_tag_str


def test_create_release_integration():
    project = MockProject()
    tag = "v1.0.1"
    name = "v1.0.1"
    message = "Bug fixes and improvements"
    ref = "commit123"
    release = ForgejoRelease.create(project, tag, name, message, ref)

    # Assertions on the created release.
    assert release.title == name
    assert release.body == message
    assert release.tag_name == tag
    assert release.url == f"http://dummy-forgejo/release/{tag}"
    expected_created = datetime.datetime.strptime(
        "2023-02-01T12:00:00Z",
        "%Y-%m-%dT%H:%M:%SZ",
    )
    assert release.created_at == expected_created
    assert release.tarball_url == f"http://dummy-forgejo/release/{tag}/tarball"

    git_tag = release.git_tag
    expected_git_tag_str = f"GitTag(name={tag}, commit_sha=abcdef7890)"
    assert str(git_tag) == expected_git_tag_str

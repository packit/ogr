# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime

import pytest

from ogr.services.forgejo.release import ForgejoProject, ForgejoRelease


class FakeRepository:
    def repo_create_release(
        self,
        owner,
        repo,
        tag_name,
        name,
        body,
        target_commitish,
        draft,
        prerelease,
    ):
        return {
            "name": name,
            "description": body,
            "tag_name": tag_name,
            "html_url": f"http://dummy-forgejo/release/{tag_name}",
            "created_at": "2023-02-01T12:00:00Z",
            "tarball_url": f"http://dummy-forgejo/release/{tag_name}/tarball",
            "commit_sha": "abcdef7890",
        }


class FakeForgejoAPI:
    def __init__(self):
        self.repository = FakeRepository()

    def repo_create_release(
        self,
        owner,
        repo,
        tag_name,
        name,
        body,
        target_commitish,
        draft,
        prerelease,
    ):
        return self.repository.repo_create_release(
            owner,
            repo,
            tag_name,
            name,
            body,
            target_commitish,
            draft,
            prerelease,
        )

    def get_releases(self, owner, repo, params=None):
        tag = params.get("tag") if params and "tag" in params else "v1.0.0"
        return [
            {
                "name": tag,
                "description": "Initial release",
                "tag_name": tag,
                "html_url": f"http://dummy-forgejo/release/{tag}",
                "created_at": "2023-01-01T12:00:00Z",
                "tarball_url": f"http://dummy-forgejo/release/{tag}/tarball",
                "commit_sha": "abcdef123456",
            },
        ]

    def get_latest_release(self, owner, repo):
        return {
            "name": "v2.0.0",
            "description": "Latest release",
            "tag_name": "v2.0.0",
            "html_url": "http://dummy-forgejo/release/v2.0.0",
            "created_at": "2023-03-01T12:00:00Z",
            "tarball_url": "http://dummy-forgejo/release/v2.0.0/tarball",
            "commit_sha": "latestcommit123",
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

    def edit_release(self, owner, repo, tag, payload):
        return {
            "name": payload.get("name"),
            "description": payload.get("body"),
            "tag_name": tag,
            "html_url": f"http://dummy-forgejo/release/{tag}",
            "created_at": "2023-04-01T12:00:00Z",
            "tarball_url": f"http://dummy-forgejo/release/{tag}/tarball",
            "commit_sha": "editedcommit456",
        }


class MockProject(ForgejoProject):
    forge_api_url = "http://dummy-forgejo/api/v1"
    owner = "dummy_owner"
    repo = "dummy_repo"
    token = "dummy_token"

    def __init__(self):
        super().__init__(api=FakeForgejoAPI())
        self.owner = "dummy_owner"
        self.repo = "dummy_repo"

    def get_auth_header(self) -> dict[str, str]:
        return {"Authorization": "Bearer dummy_token"}


@pytest.fixture(autouse=True)
def patch_pyforgejo_api(monkeypatch):
    monkeypatch.setattr("ogr.services.forgejo.release.PyforgejoApi", FakeForgejoAPI)


def test_get_release_integration():
    project = MockProject()
    tag_name = "v1.0.0"
    release = ForgejoRelease.get(project, tag_name=tag_name)

    assert release.title == "v1.0.0"
    assert release.body == "Initial release"
    assert release.tag_name == tag_name
    assert release.url == f"http://dummy-forgejo/release/{tag_name}"
    expected_created = datetime.datetime.strptime(
        "2023-01-01T12:00:00Z",
        "%Y-%m-%dT%H:%M:%SZ",
    )
    assert release.created_at == expected_created
    assert release.tarball_url == f"http://dummy-forgejo/release/{tag_name}/tarball"
    assert str(release.git_tag) == f"GitTag(name={tag_name}, commit_sha=abcdef123456)"


def test_create_release_integration():
    project = MockProject()
    tag = "v1.0.1"
    name = "v1.0.1"
    message = "Bug fixes and improvements"
    ref = "commit123"
    release = ForgejoRelease.create(project, tag, name, message, ref)

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
    assert str(release.git_tag) == f"GitTag(name={tag}, commit_sha=abcdef7890)"


def test_edit_release_integration():
    project = MockProject()
    tag_name = "v1.0.0"
    release = ForgejoRelease.get(project, tag_name=tag_name)

    release.edit_release(name="v1.0.0-updated", message="Updated release message")

    assert release.title == "v1.0.0-updated"
    assert release.body == "Updated release message"
    assert release.tag_name == "v1.0.0"
    assert str(release.git_tag) == "GitTag(name=v1.0.0, commit_sha=editedcommit456)"

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime

import responses

from ogr.services.forgejo.release import ForgejoRelease


# Create a mock project class to simulate a real project configuration.
class MockProject:
    forge_api_url = "http://dummy-forgejo/api/v1"
    owner = "dummy_owner"
    repo = "dummy_repo"

    def get_auth_header(self) -> dict[str, str]:
        return {"Authorization": "Bearer dummy_token"}


@responses.activate
def test_get_release_integration():
    project = MockProject()
    tag_name = "v1.0.0"
    # Dummy response data simulating Forgejo API output for a release.
    dummy_release = {
        "name": "v1.0.0",
        "description": "Initial release",
        "tag_name": tag_name,
        "html_url": f"http://dummy-forgejo/release/{tag_name}",
        "created_at": "2023-01-01T12:00:00Z",
        "tarball_url": f"http://dummy-forgejo/release/{tag_name}/tarball",
        "commit_sha": "abcdef123456",
    }
    url = f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/releases"
    responses.add(responses.GET, url, json=dummy_release, status=200)

    # Call the method under test.
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

    # Verify the git_tag property returns a ForgejoGitTag instance with the correct values.
    git_tag = release.git_tag
    expected_git_tag_str = f"GitTag(name={tag_name}, commit_sha=abcdef123456)"
    assert str(git_tag) == expected_git_tag_str


@responses.activate
def test_create_release_integration():
    project = MockProject()
    tag = "v1.0.1"
    name = "v1.0.1"
    message = "Bug fixes and improvements"
    ref = "commit123"
    url = f"{project.forge_api_url}/repos/{project.owner}/{project.repo}/releases"

    # Dummy response for creating a release.
    dummy_release = {
        "name": name,
        "description": message,
        "tag_name": tag,
        "html_url": f"http://dummy-forgejo/release/{tag}",
        "created_at": "2023-02-01T12:00:00Z",
        "tarball_url": f"http://dummy-forgejo/release/{tag}/tarball",
        "commit_sha": "abcdef7890",
    }
    responses.add(responses.POST, url, json=dummy_release, status=200)

    # Call the create method.
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

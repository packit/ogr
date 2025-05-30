# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.helpers import record_httpx


@record_httpx
def test_get_release(project):
    release = project.get_release(tag_name="0.1.0")
    assert release.title == "test"
    assert release.body == "testing release"


@record_httpx
def test_get_releases(project):
    releases = project.get_releases()
    assert releases
    assert len(releases) >= 9


@record_httpx
def test_create_release(project):
    releases_before = project.get_releases()
    latest_release = releases_before[0].tag_name
    count_before = len(releases_before)
    increased_release = ".".join(
        [
            latest_release.rsplit(".", 1)[0],
            str(int(latest_release.rsplit(".", 1)[1]) + 1),
        ],
    )
    release = project.create_release(
        tag=increased_release,
        name="test",
        message="testing release",
    )
    count_after = len(project.get_releases())
    assert release.tag_name == increased_release
    assert release.title == "test"
    assert release.body == "testing release"
    assert count_before + 1 == count_after


@record_httpx
def test_edit_release(project):
    release = project.get_release(tag_name="0.1.0")
    origin_name = release.title
    origin_message = release.body

    release.edit_release(
        name=f"{origin_name}-changed",
        message=f"{origin_message}-changed",
    )
    assert release.title == f"{origin_name}-changed"
    assert release.body == f"{origin_message}-changed"


@record_httpx
def test_latest_release(project):
    # check the latest release of the repo and fix version and string in the body
    last_version = "0.2.11"
    release = project.get_latest_release()
    assert release.tag_name == last_version


@record_httpx
def test_latest_release_doesnt_exist(hello_world_project):
    assert hello_world_project.get_latest_release() is None

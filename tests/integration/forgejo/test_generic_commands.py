# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


from collections.abc import Iterable

from requre.helpers import record_httpx

from ogr.abstract import CommitStatus


@record_httpx()
def test_get_commit_statuses(project):
    flags = project.get_commit_statuses(
        commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
    )

    assert isinstance(flags, Iterable)

    it = iter(flags)
    flag = next(it, None)

    assert flag.state == CommitStatus.success
    assert flag.comment == "testing status"
    assert flag.context == "test"
    assert flag.created.year == 2025


@record_httpx()
def test_set_commit_status(project):
    old_statuses = project.get_commit_statuses(
        commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
    )

    status = project.set_commit_status(
        commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
        state=CommitStatus.success,
        target_url="https://v10.next.forgejo.org/packit-validator/ogr-tests",
        description="testing status",
        context="test",
    )

    assert status
    new_statuses = project.get_commit_statuses(
        commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
    )

    old_count = sum(1 for _ in iter(old_statuses))
    new_count = sum(1 for _ in iter(new_statuses))

    assert old_count == new_count

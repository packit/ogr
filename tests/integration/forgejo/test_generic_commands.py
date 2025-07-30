# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


from collections.abc import Iterable

from requre.helpers import record_httpx

from ogr.abstract import CommitStatus


@record_httpx()
def test_get_commit_statuses(project):
    flags = project.get_commit_statuses(
        commit="24c86d0704694f686329b2ea636c5b7522cfdc40",
    )

    assert isinstance(flags, Iterable)

    it = iter(flags)
    flag = next(it)

    assert flag.state == CommitStatus.success
    assert flag.comment == "Initial commit"
    assert flag.context == "default"
    assert flag.created.year == 2019

    # assert flag.created == datetime(
    #     year=2019,
    #     month=9,
    #     day=10,
    #     hour=12,
    #     minute=28,
    #     second=?????,
    #     microsecond=?????,
    # )


@record_httpx()
def test_set_commit_status(project):
    # old_statuses = project.get_commit_statuses(
    #     commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
    # )

    status = project.set_commit_status(
        commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
        state=CommitStatus.success,
        target_url="https://v10.next.forgejo.org/packit-validator/ogr-tests",
        description="testing status",
        context="test",
    )

    assert status
    # new_statuses = project.get_commit_statuses(
    #     commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
    # )

    # todo compare length of iterables....
    # assert len(old_statuses) == len(new_statuses)

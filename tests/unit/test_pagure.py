# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from unittest import TestCase

import pytest
from flexmock import flexmock

from ogr import PagureService
from ogr.abstract import AccessLevel
from ogr.exceptions import PagureAPIException
from ogr.services.pagure.project import PagureProject


class TestPagureService(TestCase):
    def test_hostname(self):
        assert PagureService().hostname == "src.fedoraproject.org"
        assert PagureService(instance_url="https://pagure.io").hostname == "pagure.io"


def _make_pagure_project(access_users, access_groups=None):
    service = flexmock(instance_url="https://pagure.io", read_only=False)
    project = PagureProject(
        repo="test_repo",
        namespace="test_namespace",
        service=service,
    )
    project_info = {
        "access_users": access_users,
        "access_groups": access_groups or {"admin": [], "commit": [], "ticket": []},
    }
    flexmock(project).should_receive("get_project_info").and_return(project_info)
    return project


class TestPagureHasPermission:
    @pytest.mark.parametrize(
        ("access_key", "access_level", "expected"),
        [
            ("ticket", AccessLevel.pull, True),
            ("commit", AccessLevel.triage, True),
            ("ticket", AccessLevel.triage, False),
            ("commit", AccessLevel.admin, False),
            ("admin", AccessLevel.admin, True),
            ("admin", AccessLevel.maintain, True),
            ("commit", AccessLevel.maintain, False),
        ],
    )
    def test_has_permission(self, access_key, access_level, expected):
        access_users = {"owner": [], "admin": [], "commit": [], "ticket": []}
        access_users[access_key] = ["testuser"]
        project = _make_pagure_project(access_users)

        assert project.has_permission("testuser", access_level) is expected

    def test_has_permission_owner_pull(self):
        access_users = {
            "owner": ["the-owner"],
            "admin": [],
            "commit": [],
            "ticket": [],
        }
        project = _make_pagure_project(access_users)

        assert project.has_permission("the-owner", AccessLevel.pull) is True

    def test_has_permission_owner_maintain(self):
        access_users = {
            "owner": ["the-owner"],
            "admin": [],
            "commit": [],
            "ticket": [],
        }
        project = _make_pagure_project(access_users)

        assert project.has_permission("the-owner", AccessLevel.maintain) is True

    def test_has_permission_via_group(self):
        access_users = {"owner": [], "admin": [], "commit": [], "ticket": []}
        access_groups = {"admin": [], "commit": ["dev-team"], "ticket": []}
        project = _make_pagure_project(access_users, access_groups)

        mock_group = flexmock(members=["groupuser"])
        project.service.should_receive("get_group").with_args(
            "dev-team",
        ).and_return(mock_group)

        assert project.has_permission("groupuser", AccessLevel.push) is True

    def test_has_permission_unknown_user(self):
        access_users = {"owner": [], "admin": [], "commit": [], "ticket": []}
        project = _make_pagure_project(access_users)

        assert project.has_permission("nobody", AccessLevel.pull) is False

    def test_has_permission_api_error(self):
        service = flexmock(instance_url="https://pagure.io", read_only=False)
        project = PagureProject(
            repo="test_repo",
            namespace="test_namespace",
            service=service,
        )
        flexmock(project).should_receive("get_project_info").and_raise(
            PagureAPIException("Server error", response_code=500),
        )

        assert project.has_permission("anyone", AccessLevel.push) is False

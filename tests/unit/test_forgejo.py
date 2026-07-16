# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest
from flexmock import flexmock
from pyforgejo import NotFoundError

from ogr.abstract import AccessLevel
from ogr.services.forgejo.project import ForgejoProject


class TestForgejoHasPermission:
    @staticmethod
    def _make_project():
        service = flexmock()
        project = ForgejoProject(
            repo="test_repo",
            service=service,
            namespace="test_namespace",
        )
        mock_api = flexmock()
        flexmock(project).should_receive("api").and_return(mock_api)
        return project, mock_api

    @pytest.mark.parametrize(
        ("perm", "access_level", "expected"),
        [
            ("write", AccessLevel.triage, True),
            ("write", AccessLevel.push, True),
            ("read", AccessLevel.triage, False),
            ("read", AccessLevel.pull, True),
            ("admin", AccessLevel.admin, True),
            ("admin", AccessLevel.maintain, False),
            ("owner", AccessLevel.maintain, True),
            ("none", AccessLevel.pull, False),
        ],
    )
    def test_has_permission(self, perm, access_level, expected):
        project, mock_api = self._make_project()

        mock_api.should_receive("repo_get_repo_permissions").with_args(
            owner="test_namespace",
            repo="test_repo",
            collaborator="testuser",
        ).and_return(flexmock(permission=perm))

        assert project.has_permission("testuser", access_level) is expected

    def test_has_permission_nonexistent_user(self):
        project, mock_api = self._make_project()

        mock_api.should_receive("repo_get_repo_permissions").with_args(
            owner="test_namespace",
            repo="test_repo",
            collaborator="ghost",
        ).and_raise(NotFoundError("Not Found"))

        assert project.has_permission("ghost", AccessLevel.pull) is False

    def test_has_permission_none_permission(self):
        project, mock_api = self._make_project()

        mock_api.should_receive("repo_get_repo_permissions").with_args(
            owner="test_namespace",
            repo="test_repo",
            collaborator="testuser",
        ).and_return(flexmock(permission=None))

        assert project.has_permission("testuser", AccessLevel.pull) is False

    def test_has_permission_unknown_string(self):
        project, mock_api = self._make_project()

        mock_api.should_receive("repo_get_repo_permissions").with_args(
            owner="test_namespace",
            repo="test_repo",
            collaborator="testuser",
        ).and_return(flexmock(permission="custom_role"))

        assert project.has_permission("testuser", AccessLevel.pull) is False

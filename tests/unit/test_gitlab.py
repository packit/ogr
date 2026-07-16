# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from unittest import TestCase

import gitlab.const
import gitlab.exceptions
import pytest
from flexmock import flexmock

from ogr import GitlabService
from ogr.abstract import AccessLevel
from ogr.services.gitlab.project import GitlabProject


class TestGitlabService(TestCase):
    def test_hostname(self):
        assert GitlabService().hostname == "gitlab.com"
        assert (
            GitlabService(instance_url="https://gitlab.gnome.org").hostname
            == "gitlab.gnome.org"
        )


class TestGitlabHasPermission:
    @staticmethod
    def _make_project(mock_users_list_result):
        users_manager = flexmock()
        users_manager.should_receive("list").and_return(mock_users_list_result)

        gitlab_instance = flexmock(users=users_manager)
        service = flexmock(gitlab_instance=gitlab_instance)

        project = GitlabProject(
            repo="test_repo",
            service=service,
            namespace="test_namespace",
        )
        mock_gitlab_repo = flexmock(members_all=flexmock(), members=flexmock())
        flexmock(project).should_receive("gitlab_repo").and_return(
            mock_gitlab_repo,
        )
        return project, mock_gitlab_repo

    @pytest.mark.parametrize(
        ("member_access", "access_level", "expected"),
        [
            (gitlab.const.GUEST_ACCESS, AccessLevel.pull, True),
            (gitlab.const.REPORTER_ACCESS, AccessLevel.triage, True),
            (gitlab.const.REPORTER_ACCESS, AccessLevel.push, False),
            (gitlab.const.DEVELOPER_ACCESS, AccessLevel.triage, True),
            (gitlab.const.MAINTAINER_ACCESS, AccessLevel.admin, True),
            (gitlab.const.MAINTAINER_ACCESS, AccessLevel.maintain, False),
            (gitlab.const.OWNER_ACCESS, AccessLevel.maintain, True),
        ],
    )
    def test_has_permission(self, member_access, access_level, expected):
        mock_user = flexmock(id=42, username="testuser")
        project, mock_gitlab_repo = self._make_project([mock_user])

        mock_member = flexmock(access_level=member_access)
        mock_gitlab_repo.members_all.should_receive("get").with_args(
            42,
        ).and_return(mock_member)

        assert project.has_permission("testuser", access_level) is expected

    def test_has_permission_nonexistent_user(self):
        project, _ = self._make_project([])

        assert project.has_permission("ghost", AccessLevel.pull) is False

    def test_has_permission_non_member(self):
        mock_user = flexmock(id=42, username="outsider")
        project, mock_gitlab_repo = self._make_project([mock_user])

        mock_gitlab_repo.members_all.should_receive("get").with_args(
            42,
        ).and_raise(
            gitlab.exceptions.GitlabGetError("404 Not found"),
        )

        assert project.has_permission("outsider", AccessLevel.pull) is False

    def test_has_permission_username_mismatch(self):
        mock_user = flexmock(id=99, username="alice_admin")
        project, _ = self._make_project([mock_user])

        assert project.has_permission("alice", AccessLevel.pull) is False

    def test_has_permission_case_insensitive(self):
        mock_user = flexmock(id=42, username="TestUser")
        project, mock_gitlab_repo = self._make_project([mock_user])

        mock_member = flexmock(access_level=gitlab.const.DEVELOPER_ACCESS)
        mock_gitlab_repo.members_all.should_receive("get").with_args(
            42,
        ).and_return(mock_member)

        assert project.has_permission("testuser", AccessLevel.push) is True

    def test_has_permission_operation_error(self):
        mock_user = flexmock(id=42, username="testuser")
        project, mock_gitlab_repo = self._make_project([mock_user])

        mock_gitlab_repo.members_all.should_receive("get").with_args(
            42,
        ).and_raise(
            gitlab.exceptions.GitlabOperationError("500 Internal Server Error"),
        )

        assert project.has_permission("testuser", AccessLevel.pull) is False

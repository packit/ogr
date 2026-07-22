# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from unittest import TestCase

import gitlab.exceptions
from flexmock import flexmock

from ogr import GitlabService
from ogr.services.gitlab.comments import GitlabIssueComment


class TestGitlabService(TestCase):
    def test_hostname(self):
        assert GitlabService().hostname == "gitlab.com"
        assert (
            GitlabService(instance_url="https://gitlab.gnome.org").hostname
            == "gitlab.gnome.org"
        )


class TestGitlabCommentAddReaction:
    """Tests for GitlabComment.add_reaction handling of duplicate emojis."""

    def _make_comment(self, *, parent=None):
        """Create a GitlabIssueComment with a mocked raw_comment."""
        raw_comment = flexmock(
            get_id=lambda: 1,
            author={"username": "testuser"},
            created_at="2025-01-01T00:00:00Z",
        )
        return GitlabIssueComment(parent=parent, raw_comment=raw_comment)

    def test_add_reaction_duplicate_with_parent_none(self):
        """When add_reaction() catches a duplicate emoji error and _parent
        is None, it should fall back to the raw GitLab client for the
        username instead of crashing with AttributeError."""
        comment = self._make_comment(parent=None)

        # Mock awardemojis.create to raise the duplicate error
        existing_emoji = flexmock(
            attributes={"name": "+1", "user": {"username": "bot_user"}},
        )
        awardemojis = flexmock(
            create=lambda data: (_ for _ in ()).throw(
                gitlab.exceptions.GitlabCreateError(
                    "404 Award Emoji Name has already been taken",
                    404,
                    b"",
                ),
            ),
            list=lambda: [existing_emoji],
        )

        # Mock the gitlab client accessible via manager
        gitlab_user = flexmock(username="bot_user")
        gitlab_client = flexmock(user=gitlab_user)
        manager = flexmock(gitlab=gitlab_client)

        comment._raw_comment = flexmock(
            awardemojis=awardemojis,
            manager=manager,
        )

        result = comment.add_reaction("+1")
        assert result._raw_reaction is existing_emoji

    def test_add_reaction_duplicate_with_parent(self):
        """When add_reaction() catches a duplicate emoji error and _parent
        is set, it should use _parent.project to get the username."""
        mock_user = flexmock(get_username=lambda: "bot_user")
        mock_service = flexmock(user=mock_user)
        mock_project = flexmock(service=mock_service)
        mock_parent = flexmock(project=mock_project, _target_project=None)

        comment = self._make_comment(parent=mock_parent)

        existing_emoji = flexmock(
            attributes={"name": "+1", "user": {"username": "bot_user"}},
        )
        awardemojis = flexmock(
            create=lambda data: (_ for _ in ()).throw(
                gitlab.exceptions.GitlabCreateError(
                    "404 Award Emoji Name has already been taken",
                    404,
                    b"",
                ),
            ),
            list=lambda: [existing_emoji],
        )

        comment._raw_comment = flexmock(awardemojis=awardemojis)

        result = comment.add_reaction("+1")
        assert result._raw_reaction is existing_emoji

    def test_add_reaction_success(self):
        """When awardemojis.create succeeds, return the new reaction."""
        comment = self._make_comment(parent=None)

        new_emoji = flexmock(attributes={"name": "+1"})
        awardemojis = flexmock(create=lambda data: new_emoji)
        comment._raw_comment = flexmock(awardemojis=awardemojis)

        result = comment.add_reaction("+1")
        assert result._raw_reaction is new_emoji

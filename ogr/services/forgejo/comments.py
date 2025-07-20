# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import logging
from urllib.parse import urlparse

import pyforgejo
from pyforgejo.types import Comment as _ForgejoComment
from pyforgejo.types.reaction import Reaction as _ForgejoReaction

from ogr.abstract import Comment, IssueComment, PRComment, Reaction
from ogr.exceptions import OperationNotSupported

logger = logging.getLogger(__name__)


class ForgejoReaction(Reaction):
    _raw_reaction: _ForgejoReaction

    def __str__(self):
        return "Forgejo" + super().__str__()

    def delete(self):
        self._raw_reaction.delete()


class ForgejoComment(Comment):
    def _from_raw_comment(self, raw_comment: _ForgejoComment) -> None:
        self._raw_comment = raw_comment
        self._id = raw_comment.id
        self._author = raw_comment.original_author
        self._created = raw_comment.created_at
        self._edited = raw_comment.updated_at

    @property
    def body(self) -> str:
        return self._raw_comment.body

    @body.setter
    def body(self, new_body: str) -> None:
        raise OperationNotSupported

    def _get_owner_and_repo(self):
        issue_url = self._raw_comment.issue_url
        parts = urlparse(issue_url).path.strip("/").split("/")
        namespace, repo = parts[0], parts[1]
        return (namespace, repo)

    @property
    def edited(self) -> datetime.datetime:
        return self._edited

    @property
    def _client(self):
        return self._parent.project.service.api

    def get_reactions(self) -> list[Reaction]:
        client = self._client
        reactions = client.issue.get_comment_reactions(owner=self._parent.project.namespace, repo=self._parent.project.repo, id=self._id)
        return (
            ForgejoReaction(raw_reaction=reaction)
            for reaction in reactions
        )

    def add_reaction(self, reaction: str) -> Reaction:
        client = self._client
        client.issue.post_comment_reaction(owner=self._parent.project.namespace, repo=self._parent.project.repo, id=self._id, content=reaction)
        return ForgejoReaction(raw_reaction=reaction)


class ForgejoIssueComment(ForgejoComment, IssueComment):
    def __str__(self) -> str:
        return "Forgejo" + super().__str__()


class ForgejoPRComment(ForgejoComment, PRComment):
    def __str__(self) -> str:
        return "Forgejo" + super().__str__()

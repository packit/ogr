# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import logging

from pyforgejo.core.api_error import ApiError
from pyforgejo.types import Comment as _ForgejoComment
from pyforgejo.types.reaction import Reaction as _ForgejoReaction

from ogr.abstract import Comment, IssueComment, PRComment, Reaction
from ogr.services import forgejo

logger = logging.getLogger(__name__)


class ForgejoReaction(Reaction):
    def __init__(
        self,
        raw_reaction: _ForgejoReaction,
        parent: "forgejo.ForgejoComment",
    ) -> None:
        super().__init__(raw_reaction)
        self._parent = parent

    def __str__(self) -> str:
        return "Forgejo" + super().__str__()

    def delete(self) -> None:
        self._parent._client.issue.delete_comment_reaction(
            owner=self._parent._parent.project.namespace,
            repo=self._parent._parent.project.repo,
            id=self._parent._id,
        )


class ForgejoComment(Comment):
    def _from_raw_comment(self, raw_comment: _ForgejoComment) -> None:
        self._raw_comment = raw_comment
        self._id = raw_comment.id
        self._author = raw_comment.user.login
        self._created = raw_comment.created_at
        self._edited = raw_comment.updated_at

    @property
    def body(self) -> str:
        return self._raw_comment.body

    @body.setter
    def body(self, new_body: str) -> None:
        self._raw_comment = self._client.issue.edit_comment(
            owner=self._parent.project.namespace,
            repo=self._parent.project.repo,
            id=self._id,
            body=new_body,
        )

    @property
    def edited(self) -> datetime.datetime:
        return self._edited

    @property
    def _client(self):
        return self._parent.project.service.api

    def get_reactions(self) -> list[Reaction]:
        client = self._client
        try:
            reactions = client.issue.get_comment_reactions(
                owner=self._parent.project.namespace,
                repo=self._parent.project.repo,
                id=self._id,
            )

        # pyforgejo raises ApiError when no reactions are found
        except ApiError:
            return []

        return [
            ForgejoReaction(raw_reaction=reaction, parent=self)
            for reaction in reactions
        ]

    def add_reaction(self, reaction: str) -> Reaction:
        client = self._client
        raw_reaction = client.issue.post_comment_reaction(
            owner=self._parent.project.namespace,
            repo=self._parent.project.repo,
            id=self._id,
            content=reaction,
        )
        return ForgejoReaction(raw_reaction=raw_reaction, parent=self)


class ForgejoIssueComment(ForgejoComment, IssueComment):
    def __str__(self) -> str:
        return "Forgejo" + super().__str__()


class ForgejoPRComment(ForgejoComment, PRComment):
    def __str__(self) -> str:
        return "Forgejo" + super().__str__()

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import logging
from typing import Union

import gitlab.exceptions
from gitlab.v4.objects import (
    ProjectCommitComment,
    ProjectCommitDiscussionNote,
    ProjectIssueNote,
    ProjectIssueNoteAwardEmoji,
    ProjectMergeRequestAwardEmoji,
    ProjectMergeRequestNote,
)

from ogr.abstract import Comment, CommitComment, IssueComment, PRComment, Reaction
from ogr.exceptions import GitlabAPIException, OperationNotSupported

logger = logging.getLogger(__name__)


class GitlabReaction(Reaction):
    _raw_reaction: Union[
        ProjectIssueNoteAwardEmoji,
        ProjectMergeRequestAwardEmoji,
    ]

    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

    def delete(self) -> None:
        self._raw_reaction.delete()


class GitlabComment(Comment):
    def _from_raw_comment(
        self,
        raw_comment: Union[
            ProjectIssueNote,
            ProjectMergeRequestNote,
            ProjectCommitDiscussionNote,
            ProjectCommitComment,
        ],
    ) -> None:
        self._raw_comment = raw_comment
        self._id = raw_comment.get_id()
        self._author = raw_comment.author["username"]
        self._created = raw_comment.created_at

    @property
    def body(self) -> str:
        return self._raw_comment.body

    @body.setter
    def body(self, new_body: str) -> None:
        self._raw_comment.body = new_body
        self._raw_comment.save()

    @property
    def edited(self) -> datetime.datetime:
        return self._raw_comment.updated_at

    def get_reactions(self) -> list[Reaction]:
        return [
            GitlabReaction(reaction)
            for reaction in self._raw_comment.awardemojis.list()
        ]

    def add_reaction(self, reaction: str) -> GitlabReaction:
        try:
            reaction_obj = self._raw_comment.awardemojis.create({"name": reaction})
        except gitlab.exceptions.GitlabCreateError as ex:
            if "404 Award Emoji Name has already been taken" not in str(ex):
                raise GitlabAPIException() from ex

            # Take project from the parent (PR's don't have project)
            if self._parent is  None:
                raise ValueError("No parent instance")
            login = (
                getattr(self._parent, "_target_project", None) or self._parent.project
            ).service.user.get_username()

            # this happens only when the reaction was already added
            logger.info(f"The emoji {reaction} has already been taken.")
            reaction_obj = next(
                filter(
                    (
                        # we want to return that already given reaction
                        lambda item: item.attributes["name"] == reaction
                        and item.attributes["user"]["username"] == login
                    ),
                    self._raw_comment.awardemojis.list(),
                ),
            )

        return GitlabReaction(reaction_obj)


class GitlabIssueComment(GitlabComment, IssueComment):
    def __str__(self) -> str:
        return "Gitlab" + super().__str__()


class GitlabPRComment(GitlabComment, PRComment):
    def __str__(self) -> str:
        return "Gitlab" + super().__str__()


class GitlabCommitComment(GitlabComment, CommitComment):
    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

    @property
    def body(self) -> str:
        # TODO: ideally, the raw comment should be of the same type for both
        #  individual and all comments retrievals, this comes from the
        #  Gitlab API inconsistency (see get_commit_comment vs get_commit_comments)
        if isinstance(self._raw_comment, ProjectCommitComment):
            return self._raw_comment.note

        return self._raw_comment.body

    @body.setter
    def body(self, new_body: str) -> None:
        if isinstance(self._raw_comment, ProjectCommitComment):
            self._raw_comment.note = new_body
        else:
            self._raw_comment.body = new_body
        self._raw_comment.save()

    def get_reactions(self) -> list[Reaction]:
        raise OperationNotSupported(
            "Interacting with award emojis on commit comments is not supported via API.",
        )

    def add_reaction(self, reaction: str) -> GitlabReaction:
        raise OperationNotSupported(
            "Interacting with award emojis on commit comments is not supported via API.",
        )

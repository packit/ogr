# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import logging
from typing import List, Union

import gitlab.exceptions
from gitlab.v4.objects import (
    ProjectIssueNote,
    ProjectMergeRequestNote,
    ProjectIssueNoteAwardEmoji,
    ProjectMergeRequestAwardEmoji,
)

from ogr.abstract import IssueComment, PRComment, Reaction
from ogr.exceptions import GitlabAPIException

logger = logging.getLogger(__name__)


class GitlabReaction(Reaction):
    _raw_reaction: Union[ProjectIssueNoteAwardEmoji, ProjectMergeRequestAwardEmoji]

    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

    def delete(self) -> None:
        self._raw_reaction.delete()


class GitlabComment:
    def _from_raw_comment(
        self, raw_comment: Union[ProjectIssueNote, ProjectMergeRequestNote]
    ) -> None:
        self._raw_comment = raw_comment
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

    def get_reactions(self) -> List[Reaction]:
        return [
            GitlabReaction(reaction)
            for reaction in self._raw_comment.awardemojis.list()
        ]

    def add_reaction(self, reaction: str) -> GitlabReaction:
        try:
            reaction_obj = self._raw_comment.awardemojis.create({"name": reaction})
        except gitlab.exceptions.GitlabCreateError as ex:
            if "404 Award Emoji Name has already been taken" not in str(ex):
                raise GitlabAPIException(ex)

            # this happens only when the reaction was already added
            logger.info(f"The emoji {reaction} has already been taken.")
            (reaction_obj,) = filter(
                (
                    # we want to return that already given reaction
                    lambda item: item.attributes["name"] == reaction
                    and item.attributes["user"]["name"]
                    == item.awardemojis.gitlab.user.name
                ),
                self._raw_comment.awardemojis.list(),
            )

        return GitlabReaction(reaction_obj)


class GitlabIssueComment(GitlabComment, IssueComment):
    def __str__(self) -> str:
        return "Gitlab" + super().__str__()


class GitlabPRComment(GitlabComment, PRComment):
    def __str__(self) -> str:
        return "Gitlab" + super().__str__()

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import List, Union

from github.IssueComment import IssueComment as _GithubIssueComment
from github.PullRequestComment import PullRequestComment as _GithubPullRequestComment
from github.Reaction import Reaction as _Reaction

from ogr.abstract import Comment, IssueComment, PRComment, Reaction


class GithubReaction(Reaction):
    _raw_reaction: _Reaction

    def __str__(self) -> str:
        return "Github" + super().__str__()

    def delete(self) -> None:
        self._raw_reaction.delete()


class GithubComment(Comment):
    def _from_raw_comment(
        self, raw_comment: Union[_GithubIssueComment, _GithubPullRequestComment]
    ) -> None:
        self._raw_comment = raw_comment
        self._id = raw_comment.id
        self._author = raw_comment.user.login
        self._created = raw_comment.created_at

    @property
    def body(self) -> str:
        return self._raw_comment.body

    @body.setter
    def body(self, new_body: str) -> None:
        self._raw_comment.edit(new_body)

    @property
    def edited(self) -> datetime.datetime:
        return self._raw_comment.updated_at

    def get_reactions(self) -> List[Reaction]:
        return [
            GithubReaction(reaction) for reaction in self._raw_comment.get_reactions()
        ]

    def add_reaction(self, reaction: str) -> GithubReaction:
        return GithubReaction(self._raw_comment.create_reaction(reaction))


class GithubIssueComment(GithubComment, IssueComment):
    def __str__(self) -> str:
        return "Github" + super().__str__()


class GithubPRComment(GithubComment, PRComment):
    def __str__(self) -> str:
        return "Github" + super().__str__()

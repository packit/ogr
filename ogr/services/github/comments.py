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
from typing import List, Union

from github.IssueComment import IssueComment as _GithubIssueComment
from github.PullRequestComment import PullRequestComment as _GithubPullRequestComment
from github.Reaction import Reaction as _Reaction

from ogr.abstract import IssueComment, PRComment, Reaction


class GithubReaction(Reaction):
    _raw_reaction: _Reaction

    def __str__(self) -> str:
        return "Github" + super().__str__()

    def delete(self) -> None:
        self._raw_reaction.delete()


class GithubComment:
    def _from_raw_comment(
        self, raw_comment: Union[_GithubIssueComment, _GithubPullRequestComment]
    ) -> None:
        self._raw_comment = raw_comment
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

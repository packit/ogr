# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime

from pyforgejo.types.comment import Comment as FComment

from ogr.abstract import Comment, IssueComment, PRComment


class ForgejoComment(Comment):
    def _from_raw_comment(self, raw_comment: FComment) -> None:
        self._raw_comment = raw_comment
        self._id = self._raw_comment.id
        self._created = self._raw_comment.created_at
        self._author = self._raw_comment.user.login

    @property
    def body(self) -> str:
        return self._raw_comment.body

    @body.setter
    def body(self, new_body: str) -> None:
        updated_comment = self._parent.project.service.api.issue.edit_comment(
            owner=self._parent.project.namespace,
            repo=self._parent.project.repo,
            id=self._raw_comment.id,
            body=new_body,
        )
        self._raw_comment = updated_comment

    @property
    def author(self) -> str:
        return self._raw_comment.user.login

    @property
    def edited(self) -> datetime.datetime:
        return self._raw_comment.updated_at


class ForgejoIssueComment(ForgejoComment, IssueComment):
    def __str__(self):
        return "Forgejo" + super().__str__()


class ForgejoPRComment(ForgejoComment, PRComment):
    def __str__(self):
        return "Forgejo" + super().__str__()

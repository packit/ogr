# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import Any, Dict, Optional

from ogr.abstract import Comment, IssueComment, PRComment
from ogr.exceptions import OperationNotSupported


class PagureComment(Comment):
    def _from_raw_comment(self, raw_comment: Dict[str, Any]) -> None:
        self._body = raw_comment["comment"]
        self._id = raw_comment["id"]
        self._author = raw_comment["user"]["name"]
        self._created = self.__datetime_from_timestamp(raw_comment["date_created"])
        self._edited = self.__datetime_from_timestamp(raw_comment["edited_on"])

    @staticmethod
    def __datetime_from_timestamp(
        timestamp: Optional[str],
    ) -> Optional[datetime.datetime]:
        return datetime.datetime.fromtimestamp(int(timestamp)) if timestamp else None

    @property
    def body(self) -> str:
        return self._body

    @body.setter
    def body(self, new_body: str) -> None:
        raise OperationNotSupported()


class PagureIssueComment(PagureComment, IssueComment):
    def __str__(self) -> str:
        return "Pagure" + super().__str__()


class PagurePRComment(PagureComment, PRComment):
    def __str__(self) -> str:
        return "Pagure" + super().__str__()

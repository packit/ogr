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
from typing import List, Dict, Any, Union


from ogr.abstract import CommitFlag, CommitStatus
from ogr.services import pagure as ogr_pagure
from ogr.services.base import BaseCommitFlag


class PagureCommitFlag(BaseCommitFlag):
    _states = {
        "pending": CommitStatus.pending,
        "success": CommitStatus.success,
        "failure": CommitStatus.failure,
        "error": CommitStatus.error,
        "canceled": CommitStatus.canceled,
    }

    def __str__(self) -> str:
        return "Pagure" + super().__str__()

    def _from_raw_commit_flag(self):
        self.commit = self._raw_commit_flag["commit_hash"]
        self.comment = self._raw_commit_flag["comment"]
        self.state = self._state_from_str(self._raw_commit_flag["status"])
        self.context = self._raw_commit_flag["username"]
        self.url = self._raw_commit_flag["url"]

    @staticmethod
    def get(project: "ogr_pagure.PagureProject", commit: str) -> List["CommitFlag"]:
        response = project._call_project_api("c", commit, "flag")
        return [
            PagureCommitFlag(raw_commit_flag=flag, project=project)
            for flag in response["flags"]
        ]

    @staticmethod
    def set(
        project: "ogr_pagure.PagureProject",
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        percent: int = None,
        trim: bool = False,
        uid: str = None,
    ) -> "CommitFlag":
        state = PagureCommitFlag._validate_state(state)

        if trim:
            description = description[:140]

        data: Dict[str, Any] = {
            "username": context,
            "comment": description,
            "url": target_url,
            "status": state.name,
        }
        if percent:
            data["percent"] = percent
        if uid:
            data["uid"] = uid

        response = project._call_project_api(
            "c", commit, "flag", method="POST", data=data
        )
        return PagureCommitFlag(
            project=project, raw_commit_flag=response["flag"], uid=response["uid"]
        )

    @property
    def created(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            int(self._raw_commit_flag["date_created"])
        )

    @property
    def edited(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            int(self._raw_commit_flag["date_updated"])
        )

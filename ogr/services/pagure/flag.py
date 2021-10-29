# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import List, Dict, Any


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
        state: CommitStatus,
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

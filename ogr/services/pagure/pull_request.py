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
from typing import List, Optional, Dict, Any
import warnings

from ogr.abstract import PRStatus, CommitFlag
from ogr.abstract import PullRequest, PRComment
from ogr.exceptions import PagureAPIException
from ogr.services.base import BasePullRequest
from ogr.services import pagure as ogr_pagure
from ogr.services.pagure.comments import PagurePRComment

logger = logging.getLogger(__name__)


class PagurePullRequest(BasePullRequest):
    project: "ogr_pagure.PagureProject"

    def __init__(self, raw_pr, project):
        super().__init__(raw_pr, project)
        self.__dirty = False

    def __update(self):
        if self.__dirty:
            self._raw_pr = self.__call_api()
            self.__dirty = False

    @property
    def title(self) -> str:
        self.__update()
        return self._raw_pr["title"]

    @property
    def id(self) -> int:
        return self._raw_pr["id"]

    @property
    def status(self) -> PRStatus:
        self.__update()
        state = self._raw_pr["status"].lower()
        return PRStatus[state] if state != "open" else PRStatus.opened

    @property
    def url(self) -> str:
        return "/".join(
            [
                self.project.service.instance_url,
                self._raw_pr["project"]["url_path"],
                "pull-request",
                str(self.id),
            ]
        )

    @property
    def description(self) -> str:
        self.__update()
        return self._raw_pr["initial_comment"]

    @property
    def author(self) -> str:
        return self._raw_pr["user"]["name"]

    @property
    def source_branch(self) -> str:
        return self._raw_pr["branch_from"]

    @property
    def target_branch(self) -> str:
        return self._raw_pr["branch"]

    @property
    def created(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(int(self._raw_pr["date_created"]))

    def __str__(self) -> str:
        return "Pagure" + super().__str__()

    def __call_api(self, *args, **kwargs) -> dict:
        return self.project._call_project_api(
            "pull-request", str(self.id), *args, **kwargs
        )

    @staticmethod
    def create(
        project: "ogr_pagure.PagureProject",
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        data = {
            "title": title,
            "branch_to": target_branch,
            "branch_from": source_branch,
            "initial_comment": body,
        }

        caller = project
        if project.is_fork:
            data["repo_from"] = project.repo
            data["repo_from_username"] = project._user
            data["repo_from_namespace"] = project.namespace

            # running the call from the parent project
            caller = caller.parent

        response = caller._call_project_api(
            "pull-request", "new", method="POST", data=data
        )
        return PagurePullRequest(response, project)

    @staticmethod
    def get(project: "ogr_pagure.PagureProject", id: int) -> "PullRequest":
        raw_pr = project._call_project_api("pull-request", str(id))
        return PagurePullRequest(raw_pr, project)

    @staticmethod
    def get_list(
        project: "ogr_pagure.PagureProject",
        status: PRStatus = PRStatus.opened,
        assignee=None,
        author=None,
    ) -> List["PullRequest"]:
        if status == PRStatus.open:
            warnings.warn(
                "Using deprecated constant, that will be removed in 0.14.0"
                "(or 1.0.0 if it comes sooner). Please use opened.",
                DeprecationWarning,
            )
            status = PRStatus.opened

        state = status.name.capitalize() if status != PRStatus.opened else "OPEN"
        payload = {"status": state}
        if assignee is not None:
            payload["assignee"] = assignee
        if author is not None:
            payload["author"] = author

        raw_prs = project._call_project_api("pull-requests", params=payload)["requests"]
        return [PagurePullRequest(pr_dict, project) for pr_dict in raw_prs]

    def update_info(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> "PullRequest":
        try:
            data = {}
            if title:
                data["title"] = title

            if description:
                data["initial_comment"] = description

            updated_pr = self.__call_api(method="POST", data=data)
            logger.info(f"PR updated.")

            self._raw_pr = updated_pr
            return self
        except Exception as ex:
            raise PagureAPIException("there was an error while updating the PR", ex)

    def _get_all_comments(self) -> List[PRComment]:
        self.__update()
        raw_comments = self._raw_pr["comments"]
        return [
            PagurePRComment(parent=self, raw_comment=comment_dict)
            for comment_dict in raw_comments
        ]

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
        payload: Dict[str, Any] = {"comment": body}
        if commit is not None:
            payload["commit"] = commit
        if filename is not None:
            payload["filename"] = filename
        if row is not None:
            payload["row"] = row

        self.__call_api("comment", method="POST", data=payload)
        self.__dirty = True
        return PagurePRComment(
            parent=self, body=body, author=self.project.service.user.get_username()
        )

    def close(self) -> "PullRequest":
        return_value = self.__call_api("close", method="POST")

        if return_value["message"] != "Pull-request closed!":
            raise PagureAPIException(return_value["message"])

        self.__dirty = True
        return self

    def merge(self) -> "PullRequest":
        return_value = self.__call_api("merge", method="POST")

        if return_value["message"] != "Changes merged!":
            raise PagureAPIException(return_value["message"])

        self.__dirty = True
        return self

    def get_statuses(self) -> List[CommitFlag]:
        self.__update()
        return self.project.get_commit_statuses(self._raw_pr["commit_stop"])

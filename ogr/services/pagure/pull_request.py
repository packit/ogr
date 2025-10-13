# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import logging
from collections.abc import Iterable
from http import HTTPStatus
from time import sleep
from typing import Any, Optional, Union

from ogr.abstract import (
    CommitFlag,
    CommitStatus,
    PRComment,
    PRLabel,
    PRStatus,
    PullRequest,
)
from ogr.exceptions import PagureAPIException
from ogr.services import pagure as ogr_pagure
from ogr.services.base import BasePullRequest
from ogr.services.pagure.comments import PagurePRComment
from ogr.services.pagure.label import PagurePRLabel

logger = logging.getLogger(__name__)


class PagurePullRequest(BasePullRequest):
    _target_project: "ogr_pagure.PagureProject"
    _source_project: "ogr_pagure.PagureProject" = None

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

    @title.setter
    def title(self, new_title: str) -> None:
        self.update_info(title=new_title)

    @property
    def id(self) -> int:
        return self._raw_pr["id"]

    @property
    def status(self) -> PRStatus:
        self.__update()
        return PRStatus[self._raw_pr["status"].lower()]

    @property
    def url(self) -> str:
        return "/".join(
            [
                self.target_project.service.instance_url,
                self._raw_pr["project"]["url_path"],
                "pull-request",
                str(self.id),
            ],
        )

    @property
    def description(self) -> str:
        self.__update()
        return self._raw_pr["initial_comment"]

    @description.setter
    def description(self, new_description: str) -> None:
        self.update_info(description=new_description)

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

    @property
    def diff_url(self) -> str:
        return f"{self.url}#request_diff"

    @property
    def commits_url(self) -> str:
        return f"{self.url}#commit_list"

    @property
    def patch(self) -> bytes:
        request_response = self._target_project._call_project_api_raw(
            "pull-request",
            f"{self.id}.patch",
            add_api_endpoint_part=False,
        )
        if request_response.status_code != HTTPStatus.OK:
            raise PagureAPIException(
                f"Cannot get patch from {self.url}.patch because {request_response.reason}.",
                response_code=request_response.status_code,
            )
        return request_response.content

    @property
    def head_commit(self) -> str:
        return self._raw_pr["commit_stop"]

    @property
    def source_project(self) -> "ogr_pagure.PagureProject":
        if self._source_project is None:
            source = self._raw_pr["repo_from"]
            source_project_info = {
                "repo": source["name"],
                "namespace": source["namespace"],
            }

            if source["parent"] is not None:
                source_project_info["is_fork"] = True
                source_project_info["username"] = source["user"]["name"]

            self._source_project = self._target_project.service.get_project(
                **source_project_info,
            )

        return self._source_project

    @property
    def closed_by(self) -> Optional[str]:
        closed_by = self._raw_pr["closed_by"]
        return closed_by["name"] if closed_by else None

    @property
    def labels(self) -> list[PRLabel]:
        return [PagurePRLabel(label, self) for label in self._raw_pr["tags"]]

    def __str__(self) -> str:
        return "Pagure" + super().__str__()

    def __call_api(self, *args, **kwargs) -> dict:
        return self._target_project._call_project_api(
            "pull-request",
            str(self.id),
            *args,
            **kwargs,
        )

    @staticmethod
    def create(
        project: "ogr_pagure.PagureProject",
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
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
        elif fork_username:
            fork_project = project.service.get_project(
                username=fork_username,
                repo=project.repo,
                namespace=project.namespace,
                is_fork=True,
            )
            data["repo_from_username"] = fork_username
            data["repo_from"] = fork_project.repo
            data["repo_from_namespace"] = fork_project.namespace

        response = caller._call_project_api(
            "pull-request",
            "new",
            method="POST",
            data=data,
        )
        return PagurePullRequest(response, caller)

    @staticmethod
    def get(project: "ogr_pagure.PagureProject", pr_id: int) -> "PullRequest":
        raw_pr = project._call_project_api("pull-request", str(pr_id))
        return PagurePullRequest(raw_pr, project)

    @staticmethod
    def get_files_diff(
        project: "ogr_pagure.PagureProject",
        pr_id: int,
        retries: int = 0,
        wait_seconds: int = 3,
    ) -> dict:
        """
        Retrieve pull request diff statistics.

        Pagure API tends to return ENOPRSTATS error when a pull request is transitioning
        from open to other states, so you can use `retries` and `wait_seconds` to try to
        mitigate that.


        Args:
            project: Pagure project.
            pr_id: Pull request ID.
            retries: Number of extra attempts.
            wait_seconds: Delay between attempts.
        """
        attempt = 1
        while True:
            try:
                return project._call_project_api(
                    "pull-request",
                    str(pr_id),
                    "diffstats",
                    method="GET",
                )
            except PagureAPIException as ex:  # noqa PERF203
                if "No statistics" in ex.pagure_error:
                    # this may be a race condition, try once more
                    logger.info(
                        f"While retrieving PR diffstats Pagure returned ENOPRSTATS.\n{ex}",
                    )
                    if attempt <= retries:
                        attempt += 1
                        logger.info(
                            f"Trying again; attempt={attempt} after {wait_seconds} seconds",
                        )
                        sleep(wait_seconds)
                        continue
                raise ex

    @staticmethod
    def get_list(
        project: "ogr_pagure.PagureProject",
        status: PRStatus = PRStatus.open,
        assignee=None,
        author=None,
    ) -> list["PullRequest"]:
        payload = {"page": 1, "status": status.name.capitalize()}
        if assignee is not None:
            payload["assignee"] = assignee
        if author is not None:
            payload["author"] = author

        raw_prs = []
        while True:
            page_result = project._call_project_api("pull-requests", params=payload)
            raw_prs += page_result["requests"]
            if not page_result["pagination"]["next"]:
                break

            # mypy don't know that key "page" really contains int...
            payload["page"] += 1  # type: ignore

        return [PagurePullRequest(pr_dict, project) for pr_dict in raw_prs]

    def update_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PullRequest":
        try:
            data = {"title": title if title else self.title}

            if description:
                data["initial_comment"] = description

            updated_pr = self.__call_api(method="POST", data=data)
            logger.info("PR updated.")

            self._raw_pr = updated_pr
            return self
        except Exception as ex:
            raise PagureAPIException("there was an error while updating the PR") from ex

    def _get_all_comments(self, reverse: bool = False) -> Iterable[PRComment]:
        self.__update()
        raw_comments = self._raw_pr["comments"]
        if reverse:
            raw_comments = reversed(raw_comments)

        return (
            PagurePRComment(parent=self, raw_comment=comment_dict)
            for comment_dict in raw_comments
        )

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
        payload: dict[str, Any] = {"comment": body}
        if commit is not None:
            payload["commit"] = commit
        if filename is not None:
            payload["filename"] = filename
        if row is not None:
            payload["row"] = row

        self.__call_api("comment", method="POST", data=payload)
        self.__dirty = True
        return PagurePRComment(
            parent=self,
            body=body,
            author=self.target_project.service.user.get_username(),
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

    def get_statuses(self) -> Union[list[CommitFlag], Iterable[CommitFlag]]:
        self.__update()
        return self.target_project.get_commit_statuses(self._raw_pr["commit_stop"])

    def set_flag(
        self,
        username: str,
        comment: str,
        url: str,
        status: Optional[CommitStatus] = None,
        percent: Optional[int] = None,
        uid: Optional[str] = None,
    ) -> dict:
        """
        Set a flag on a pull-request to display results or status of CI tasks.

        See "Flag a pull-request" at https://pagure.io/api/0/#pull_requests-tab
        for a full description of the parameters.

        Args:
            username: The name of the application to be presented to users
                on the pull request page.
            comment: A short message summarizing the presented results.
            url: A URL to the result of this flag.
            status: The status to be displayed for this flag.
            percent: A percentage of completion compared to the goal.
            uid: A unique identifier used to identify a flag on the pull-request.

        Returns:
            Dictionary with the response received from Pagure.
        """
        data: dict[str, Union[str, int]] = {
            "username": username,
            "comment": comment,
            "url": url,
        }
        if status is not None:
            data["status"] = status.name
        if percent is not None:
            data["percent"] = percent
        if uid is not None:
            data["uid"] = uid
        return self.__call_api("flag", method="POST", data=data)

    def get_comment(self, comment_id: int) -> PRComment:
        for comment in self._get_all_comments():
            if comment.id == comment_id:
                return comment

        raise PagureAPIException(
            f"No comment with id#{comment_id} in PR#{self.id} found.",
            response_code=404,
        )

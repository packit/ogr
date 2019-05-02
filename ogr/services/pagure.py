import datetime
import logging
from typing import List, Optional, Dict, Type

from ogr.abstract import PRStatus
from ogr.abstract import PullRequest, PRComment
from ogr.services.base import BaseGitService, BaseGitProject, BaseGitUser
from ogr.services.our_pagure import OurPagure
from ogr.mock_core import readonly, GitProjectReadOnly, PersistentObjectStorage
from ogr.services.mock.pagure_mock import get_Pagure_class
from ogr.exceptions import OurPagureRawRequest

logger = logging.getLogger(__name__)


class PagureService(BaseGitService):
    # class parameter could be use to mock Pagure class api
    pagure_class: Type[OurPagure]
    persistent_storage: Optional[PersistentObjectStorage] = None

    def __init__(
        self,
        token: str = None,
        instance_url: str = "https://src.fedoraproject.org",
        read_only: bool = False,
        persistent_storage: Optional[PersistentObjectStorage] = None,
        **kwargs,
    ) -> None:
        super().__init__()
        self.instance_url = instance_url
        self._token = token
        self.pagure_kwargs = kwargs
        # it could be set as class parameter too, could be used for mocking in other projects
        if persistent_storage:
            self.persistent_storage = persistent_storage
        if self.persistent_storage:
            self.pagure_class = get_Pagure_class(self.persistent_storage)
        else:
            self.pagure_class = OurPagure
        self.pagure = self.pagure_class(
            pagure_token=token, instance_url=instance_url, **kwargs
        )
        self.read_only = read_only

    def get_project(self, **kwargs) -> "PagureProject":
        project_kwargs = self.pagure_kwargs.copy()
        project_kwargs.update(kwargs)
        return PagureProject(
            instance_url=self.instance_url,
            token=self._token,
            service=self,
            read_only=self.read_only,
            **project_kwargs,
        )

    @property
    def user(self) -> "PagureUser":
        return PagureUser(service=self)

    def change_token(self, new_token: str) -> None:
        """
        Change an API token.

        Only for this instance and newly created Projects via get_project.
        """
        self._token = new_token
        self.pagure.change_token(new_token)


class PagureProject(BaseGitProject):
    service: PagureService

    def __init__(
        self,
        repo: str,
        namespace: str,
        service: PagureService,
        username: Optional[str] = None,
        instance_url: Optional[str] = None,
        token: Optional[str] = None,
        is_fork: bool = False,
        read_only: bool = False,
        **kwargs,
    ) -> None:
        if is_fork and username:
            complete_namespace = f"fork/{username}/{namespace}"
        else:
            complete_namespace = namespace

        super().__init__(repo=repo, namespace=complete_namespace, service=service)

        self.instance_url = instance_url
        self._token = token
        self.service = service
        self._pagure_kwargs = kwargs
        if username:
            self._pagure_kwargs["username"] = username

        self._pagure = self.service.pagure_class(
            token=token,
            pagure_repository=f"{namespace}/{self.repo}",
            namespace=namespace,
            fork_username=username if is_fork else None,
            instance_url=instance_url,
            **kwargs,
        )
        self.read_only = read_only

    def __str__(self) -> str:
        return f"namespace={self.namespace} repo={self.repo}"

    def __repr__(self) -> str:
        return f"PagureProject(namespace={self.namespace}, repo={self.repo})"

    def get_branches(self) -> List[str]:
        return self._pagure.get_branches()

    def get_description(self) -> str:
        return self._pagure.get_project_description()

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List[PullRequest]:
        status_str = status.name.lower().capitalize()
        raw_prs = self._pagure.list_requests(status=status_str)
        prs = [self._pr_from_pagure_dict(pr_dict) for pr_dict in raw_prs]
        return prs

    def get_pr_info(self, pr_id: int) -> PullRequest:
        pr_dict = self._pagure.request_info(request_id=pr_id)
        result = self._pr_from_pagure_dict(pr_dict)
        return result

    def _get_all_pr_comments(self, pr_id: int) -> List[PRComment]:
        raw_comments = self._pagure.request_info(request_id=pr_id)["comments"]

        parsed_comments = [
            self._prcomment_from_pagure_dict(comment_dict)
            for comment_dict in raw_comments
        ]
        return parsed_comments

    @readonly(return_function=GitProjectReadOnly.pr_comment)
    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
    ) -> PRComment:
        return self._pagure.comment_request(
            request_id=pr_id, body=body, commit=commit, filename=filename, row=row
        )

    @readonly(return_function=GitProjectReadOnly.pr_close)
    def pr_close(self, pr_id: int) -> PullRequest:
        return self._pagure.close_request(request_id=pr_id)

    @readonly(return_function=GitProjectReadOnly.pr_merge)
    def pr_merge(self, pr_id: int) -> PullRequest:
        return self._pagure.merge_request(request_id=pr_id)

    @readonly(return_function=GitProjectReadOnly.pr_create)
    def pr_create(
        self, title: str, body: str, target_branch: str, source_branch: str
    ) -> PullRequest:
        pr_info = self._pagure.create_request(
            title=title,
            body=body,
            target_branch=target_branch,
            source_branch=source_branch,
        )
        pr_object = self._pr_from_pagure_dict(pr_info)
        return pr_object

    @readonly(return_function=GitProjectReadOnly.fork_create)
    def fork_create(self) -> "PagureProject":
        self._pagure.create_fork()
        return self._construct_fork_project()

    def _construct_fork_project(self) -> "PagureProject":
        kwargs = self._pagure_kwargs.copy()
        kwargs.update(
            repo=self.repo,
            namespace=self.namespace,
            instance_url=self.instance_url,
            token=self._token,
            is_fork=True,
            read_only=self.read_only,
        )
        kwargs.setdefault("username", self.service.user.get_username())

        fork_project = PagureProject(service=self.service, **kwargs)

        return fork_project

    def get_fork(self, create: bool = True) -> Optional["PagureProject"]:
        """
        Provide GitProject instance of a fork of this project.

        Returns None if this is a fork.

        :param create: create a fork if it doesn't exist
        :return: instance of GitProject or None
        """
        if not self.is_forked():
            if create:
                return self.fork_create()
            else:
                logger.info(
                    f"Fork of {self.repo}"
                    " does not exist and we were asked not to create it."
                )
                return None
        return self._construct_fork_project()

    def exists(self):
        return self._pagure.project_exists()

    def is_forked(self) -> bool:
        """
        Is this repo forked by the authenticated user?

        :return: if yes, return True
        """
        f = self._construct_fork_project()
        return bool(f.exists() and f.parent)

    @property
    def is_fork(self) -> bool:
        return "fork" in self.namespace

    @property
    def parent(self) -> Optional["PagureProject"]:
        """
        Return parent project if this project is a fork, otherwise return None
        """
        if self.is_fork:
            parent = self._pagure.get_parent()
            kwargs = self._pagure_kwargs.copy()
            kwargs.update(
                repo=self.repo,
                namespace=parent["namespace"],
                instance_url=self.instance_url,
                token=self._token,
            )
            kwargs.setdefault("username", self.service.user.get_username())

            parent_project = PagureProject(service=self.service, **kwargs)
            return parent_project
        return None

    def get_git_urls(self) -> Dict[str, str]:
        return self._pagure.get_git_urls()

    def get_commit_flags(self, commit: str) -> List[dict]:
        return self._pagure.get_commit_flags(commit=commit)

    def _pr_from_pagure_dict(self, pr_dict: dict) -> PullRequest:
        return PullRequest(
            title=pr_dict["title"],
            id=pr_dict["id"],
            status=PRStatus[pr_dict["status"].lower()],
            url="/".join(
                [
                    self.instance_url,
                    pr_dict["project"]["url_path"],
                    "pull-request",
                    str(pr_dict["id"]),
                ]
            ),
            description=pr_dict["initial_comment"],
            author=pr_dict["user"]["name"],
            source_branch=pr_dict["branch_from"],
            target_branch=pr_dict["branch"],
            created=datetime.datetime.fromtimestamp(int(pr_dict["date_created"])),
        )

    @staticmethod
    def _prcomment_from_pagure_dict(comment_dict: dict) -> PRComment:
        return PRComment(
            comment=comment_dict["comment"],
            author=comment_dict["user"]["name"],
            created=datetime.datetime.fromtimestamp(int(comment_dict["date_created"])),
            edited=datetime.datetime.fromtimestamp(int(comment_dict["edited_on"]))
            if comment_dict["edited_on"]
            else None,
        )

    def change_token(self, new_token: str) -> None:
        """
        Change an API token.

        Only for this instance.
        """
        self._token = new_token
        self._pagure.change_token(new_token)

    def get_file_content(self, path: str, ref="master") -> str:
        try:
            content = self._pagure.get_raw_request(
                "raw", ref, "f", path, api_url=False, repo_name=True, namespace=True
            )
        except OurPagureRawRequest as ex:
            raise FileNotFoundError(f"File '{path}' on {ref} not found", ex)
        return content


class PagureUser(BaseGitUser):
    service: PagureService

    def __init__(self, service: PagureService) -> None:
        super().__init__(service=service)

    def get_username(self) -> str:
        return self.service.pagure.whoami()

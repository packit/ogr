import datetime
import logging
from typing import List, Optional, Dict

from ogr.abstract import PRStatus
from ogr.abstract import PullRequest, PRComment
from ogr.services.base import BaseGitService, BaseGitProject, BaseGitUser
from ogr.services.our_pagure import OurPagure

logger = logging.getLogger(__name__)


class PagureService(BaseGitService):
    def __init__(
        self,
        token: str = None,
        instance_url: str = "https://src.fedoraproject.org",
        **kwargs,
    ) -> None:
        super().__init__()
        self.instance_url = instance_url
        self._token = token
        self.pagure_kwargs = kwargs

        self.pagure = OurPagure(pagure_token=token, instance_url=instance_url, **kwargs)

    def get_project(self, **kwargs) -> "PagureProject":
        project_kwargs = self.pagure_kwargs.copy()
        project_kwargs.update(kwargs)
        return PagureProject(
            instance_url=self.instance_url,
            token=self._token,
            service=self,
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
        **kwargs,
    ) -> None:
        if is_fork and username:
            complete_namespace = f"fork/{username}/{namespace}"
        else:
            complete_namespace = namespace

        super().__init__(repo=repo, namespace=complete_namespace, service=service)

        self.instance_url = instance_url
        self._token = token

        self._pagure_kwargs = kwargs
        if username:
            self._pagure_kwargs["username"] = username

        self._pagure = OurPagure(
            pagure_token=token,
            pagure_repository=f"{namespace}/{self.repo}",
            namespace=namespace,
            fork_username=username if is_fork else None,
            instance_url=instance_url,
            **kwargs,
        )

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

    def pr_close(self, pr_id: int) -> PullRequest:
        return self._pagure.close_request(request_id=pr_id)

    def pr_merge(self, pr_id: int) -> PullRequest:
        return self._pagure.merge_request(request_id=pr_id)

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

    def fork_create(self) -> None:
        self._pagure.create_fork()

    def get_fork(self) -> Optional["PagureProject"]:
        """
        PagureRepo instance of the fork of this repo.
        """
        kwargs = self._pagure_kwargs.copy()
        kwargs.update(
            repo=self.repo,
            namespace=self.namespace,
            instance_url=self.instance_url,
            token=self._token,
            is_fork=True,
        )
        if "username" not in kwargs:
            kwargs["username"] = self.service.user.get_username()

        fork_project = PagureProject(service=self.service, **kwargs)
        try:
            if fork_project.exists() and fork_project._pagure.get_parent():
                return fork_project
        except Exception:
            return None
        return None

    def exists(self):
        return self._pagure.project_exists()

    @property
    def is_fork(self) -> bool:
        return "fork" in self.namespace

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

        result = self._pagure.get_raw_request(
            "raw", ref, "f", path, api_url=False, repo_name=True, namespace=True
        )
        if not result and result.reason == "NOT FOUND":
            raise FileNotFoundError(f"File '{path}' on {ref} not found")
        return result.content.decode()


class PagureUser(BaseGitUser):
    service: PagureService

    def __init__(self, service: PagureService) -> None:
        super().__init__(service=service)

    def get_username(self) -> str:
        return self.service.pagure.whoami()

import logging
from typing import Optional, Dict, List

import github
from github import UnknownObjectException, IssueComment as GithubIssueComment
from github.GitRelease import GitRelease as GithubRelease
from github.PullRequest import PullRequest as GithubPullRequest

from ogr.abstract import GitUser, GitProject, PullRequest, PRComment, PRStatus, Release
from ogr.services.base import BaseGitService, BaseGitProject, BaseGitUser

logger = logging.getLogger(__name__)


class GithubService(BaseGitService):
    def __init__(self, token=None):
        super().__init__()
        self._token = token
        self.github = github.Github(login_or_token=self._token)

    def get_project(
        self, repo=None, namespace=None, is_fork=False, **kwargs
    ) -> "GithubProject":
        if is_fork:
            namespace = self.user.get_username()
        return GithubProject(repo=repo, namespace=namespace, service=self, **kwargs)

    @property
    def user(self) -> GitUser:
        return GithubUser(service=self)

    def change_token(self, new_token: str) -> None:
        self._token = new_token
        self.github = github.Github(login_or_token=self._token)


class GithubProject(BaseGitProject):
    def __init__(self, repo: str, service: GithubService, namespace: str, **_) -> None:
        super().__init__(repo, service, namespace)
        self.github_repo = service.github.get_repo(
            full_name_or_id=f"{namespace}/{repo}"
        )

    def is_forked(self) -> bool:
        pass

    @property
    def is_fork(self) -> bool:
        return self.github_repo.fork

    def get_branches(self) -> List[str]:
        return [branch.name for branch in self.github_repo.get_branches()]

    def get_description(self) -> str:
        return self.github_repo.description

    def get_fork(self) -> Optional[GitProject]:
        raise NotImplementedError

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List[PullRequest]:
        prs = self.github_repo.get_pulls(
            state=status.name, sort="updated", direction="desc"
        )
        try:
            return [self._pr_from_github_object(pr) for pr in prs]
        except UnknownObjectException:
            return []

    def get_pr_info(self, pr_id: int) -> PullRequest:
        pr = self.github_repo.get_pull(number=pr_id)
        return self._pr_from_github_object(pr)

    def _get_all_pr_comments(self, pr_id: int) -> List[PRComment]:
        pr = self.github_repo.get_pull(number=pr_id)
        return [
            self._prcomment_from_github_object(raw_comment)
            for raw_comment in pr.get_issue_comments()
        ]

    def pr_create(
        self, title: str, body: str, target_branch: str, source_branch: str
    ) -> PullRequest:
        created_pr = self.github_repo.create_pull(
            title=title, body=body, base=target_branch, head=source_branch
        )
        return self._pr_from_github_object(created_pr)

    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
    ) -> PRComment:
        raise NotImplementedError

    def pr_close(self, pr_id: int) -> PullRequest:
        raise NotImplementedError

    def pr_merge(self, pr_id: int) -> PullRequest:
        closed_pr = self.github_repo.get_pull(number=pr_id).merge()
        return self._pr_from_github_object(closed_pr)

    def get_git_urls(self) -> Dict[str, str]:
        return {"git": self.github_repo.clone_url, "ssh": self.github_repo.ssh_url}

    def fork_create(self):
        raise NotImplementedError

    def change_token(self, new_token: str):
        raise NotImplementedError

    def get_file_content(self, path: str, ref="master") -> str:
        try:
            return self.github_repo.get_contents(
                path=path, ref=ref
            ).decoded_content.decode()
        except Exception as ex:
            raise FileNotFoundError(f"File '{path}' on {ref} not found", ex)

    def _pr_from_github_object(self, github_pr: GithubPullRequest) -> PullRequest:
        return PullRequest(
            title=github_pr.title,
            id=github_pr.id,
            status=PRStatus[github_pr.state],
            url=github_pr.url,
            description=github_pr.body,
            author=github_pr.user.name,
            source_branch=github_pr.head.ref,
            target_branch=github_pr.base.ref,
            created=github_pr.created_at,
        )

    @staticmethod
    def _prcomment_from_github_object(raw_comment: GithubIssueComment) -> PRComment:
        return PRComment(
            comment=raw_comment.body,
            author=raw_comment.user.login,
            created=raw_comment.created_at,
            edited=raw_comment.updated_at,
        )

    @staticmethod
    def _release_from_github_object(raw_release: GithubRelease) -> Release:
        """
        Get ogr.abstract.Release object from github.GithubRelease
        :param raw_release: GithubRelease, object from Github API
        https://developer.github.com/v3/repos/releases/
        :return: Release, example(type, value):
        title: str, "0.1.0"
        body: str, "Description of the release"
        tag_name: str, "v1.0.0"
        url: str, "https://api.github.com/repos/octocat/Hello-World/releases/1"
        created_at: datetime.datetime, 2018-09-19 12:56:26
        tarball_url: str, "https://api.github.com/repos/octocat/Hello-World/tarball/v1.0.0"
        """
        return Release(
            title=raw_release.title,
            body=raw_release.body,
            tag_name=raw_release.tag_name,
            url=raw_release.url,
            created_at=raw_release.created_at,
            tarball_url=raw_release.tarball_url,
        )

    def get_labels(self):
        """
        Get list of labels in the repository.
        :return: [Label]
        """
        return list(self.github_repo.get_labels())

    def update_labels(self, labels):
        """
        Update the labels of the repository. (No deletion, only add not existing ones.)

        :param labels: [str]
        :return: int - number of added labels
        """
        current_label_names = [l.name for l in list(self.github_repo.get_labels())]
        changes = 0
        for label in labels:
            if label.name not in current_label_names:
                color = self._normalize_label_color(color=label.color)
                self.github_repo.create_label(
                    name=label.name, color=color, description=label.description or ""
                )

                changes += 1
        return changes

    @staticmethod
    def _normalize_label_color(color):
        if color.startswith("#"):
            return color[1:]
        return color

    def get_release(self, identifier: int) -> Release:
        release = self.github_repo.get_release(id=identifier)
        return self._release_from_github_object(raw_release=release)

    def get_releases(self) -> List[Release]:
        releases = self.github_repo.get_releases()
        return [
            self._release_from_github_object(raw_release=release)
            for release in releases
        ]


class GithubUser(BaseGitUser):
    service: GithubService

    def __init__(self, service: GithubService) -> None:
        super().__init__(service=service)

    def get_username(self) -> str:
        return self.service.github.get_user().login

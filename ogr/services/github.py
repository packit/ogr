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

import logging
from typing import Optional, Dict, List, Type, Set

import github
from github import (
    UnknownObjectException,
    IssueComment as GithubIssueComment,
    Repository,
    CommitComment as GithubCommitComment,
)
from github.GitRelease import GitRelease as GithubRelease
from github.Issue import Issue as GithubIssue
from github.Label import Label as GithubLabel
from github.PullRequest import PullRequest as GithubPullRequest

from ogr import BetterGithubIntegration
from ogr.abstract import (
    GitUser,
    Issue,
    IssueComment,
    IssueStatus,
    PullRequest,
    PRComment,
    PRStatus,
    Release,
    CommitComment,
    GitTag,
    CommitFlag,
)
from ogr.exceptions import GithubAPIException
from ogr.factory import use_for_service
from ogr.read_only import if_readonly, GitProjectReadOnly
from ogr.services.base import BaseGitService, BaseGitProject, BaseGitUser

logger = logging.getLogger(__name__)


@use_for_service("github.com")
class GithubService(BaseGitService):
    # class parameter could be used to mock Github class api
    github_class: Type[github.Github]
    instance_url = "https://github.com"

    def __init__(
        self,
        token=None,
        read_only=False,
        github_app_id: str = None,
        github_app_private_key: str = None,
        **_,
    ):
        super().__init__()
        self.token = token

        # Authentication via GitHub app
        self.github_app_id = github_app_id
        self.github_app_private_key = github_app_private_key

        self.github = github.Github(login_or_token=self.token)
        self.read_only = read_only

    def __str__(self) -> str:
        return f"GithubService(read_only={self.read_only})"

    def __eq__(self, o: object) -> bool:
        if not issubclass(o.__class__, GithubService):
            return False

        return self.token == o.token and self.read_only == o.read_only  # type: ignore

    def get_project(
        self, repo=None, namespace=None, is_fork=False, **kwargs
    ) -> "GithubProject":
        if is_fork:
            namespace = self.user.get_username()
        return GithubProject(
            repo=repo,
            namespace=namespace,
            service=self,
            read_only=self.read_only,
            **kwargs,
        )

    @property
    def user(self) -> GitUser:
        return GithubUser(service=self)

    def change_token(self, new_token: str) -> None:
        self.token = new_token
        self.github = github.Github(login_or_token=self.token)


class GithubProject(BaseGitProject):
    service: GithubService

    def __init__(
        self,
        repo: str,
        service: GithubService,
        namespace: str,
        github_repo: Repository = None,
        read_only: bool = False,
        **unprocess_kwargs,
    ) -> None:
        if unprocess_kwargs:
            logger.warning(
                f"GithubProject will not process these kwargs: {unprocess_kwargs}"
            )
        super().__init__(repo, service, namespace)
        self._github_repo = github_repo
        self.read_only = read_only

        self._github_instance = None

    @property
    def github_instance(self):
        if not self._github_instance:
            if self.service.github_app_id and self.service.github_app_private_key:
                integration = BetterGithubIntegration(
                    self.service.github_app_id, self.service.github_app_private_key
                )
                inst_id = integration.get_installation(
                    self.namespace, self.repo
                ).id.value
                inst_auth = integration.get_access_token(inst_id)
                self._github_instance = github.Github(login_or_token=inst_auth.token)
            else:
                self._github_instance = self.service.github

        return self._github_instance

    @property
    def github_repo(self):
        if not self._github_repo:
            self._github_repo = self.github_instance.get_repo(
                full_name_or_id=f"{self.namespace}/{self.repo}"
            )
        return self._github_repo

    def __str__(self) -> str:
        return f'GithubProject(namespace="{self.namespace}", repo="{self.repo}")'

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, GithubProject):
            return False

        return (
            self.repo == o.repo
            and self.namespace == o.namespace
            and self.service == o.service
            and self.read_only == o.read_only
        )

    def _construct_fork_project(self) -> Optional["GithubProject"]:
        gh_user = self.github_instance.get_user()
        user_login = gh_user.login
        try:
            project = GithubProject(
                self.repo, self.service, namespace=user_login, read_only=self.read_only
            )
            if not project.github_repo:
                # The github_repo attribute is lazy.
                return None
            return project
        except github.GithubException as ex:
            logger.debug(f"Project {self.repo}/{user_login} does not exist: {ex}")
            return None

    def is_forked(self) -> bool:
        """
        Is this repo forked by the authenticated user?

        :return: if yes, return True
        """
        return bool(self._construct_fork_project())

    @property
    def is_fork(self) -> bool:
        """
        Is this repository a fork?

        :return: True if it is
        """
        return self.github_repo.fork

    @property
    def parent(self) -> Optional["GithubProject"]:
        """
        Return parent project if this project is a fork, otherwise return None
        """
        if self.is_fork:
            parent = self.github_repo.parent
            return GithubProject(parent.name, self.service, parent.owner.login)
        return None

    def get_branches(self) -> List[str]:
        return [branch.name for branch in self.github_repo.get_branches()]

    def get_description(self) -> str:
        return self.github_repo.description

    def get_fork(self, create: bool = True) -> Optional["GithubProject"]:
        """
        Provide GithubProject instance of a fork of this project.

        Returns None if this is a fork.

        :param create: create a fork if it doesn't exist
        :return: instance of GithubProject
        """
        username = self.service.user.get_username()
        for fork in self.get_forks():
            if fork.github_repo.owner.login == username:
                return fork

        if not self.is_forked():
            if create:
                return self.fork_create()
            else:
                logger.info(
                    f"Fork of {self.github_repo.full_name}"
                    " does not exist and we were asked not to create it."
                )
                return None
        return self._construct_fork_project()

    def get_owners(self) -> List[str]:
        # in case of github, repository has only one owner
        return [self.github_repo.owner.login]

    def who_can_close_issue(self) -> Set[str]:
        try:
            collaborators = self._get_collaborators_with_permission()
        except github.GithubException:
            logger.debug(
                f"Current Github token must have push access to view repository permissions."
            )
            return set()

        usernames = []
        for login, permission in collaborators.items():
            if permission in ["admin", "write"]:
                usernames.append(login)

        return set(usernames)

    def who_can_merge_pr(self) -> Set[str]:
        try:
            collaborators = self._get_collaborators_with_permission()
        except github.GithubException:
            logger.debug(
                f"Current Github token must have push access to view repository permissions."
            )
            return set()

        usernames = []
        for login, permission in collaborators.items():
            if permission in ["admin", "write"]:
                usernames.append(login)

        return set(usernames)

    def can_close_issue(self, username: str, issue: Issue) -> bool:
        allowed_users = self.who_can_close_issue()

        if username in allowed_users:
            return True
        if username == issue.author:
            return True

        return False

    def can_merge_pr(self, username) -> bool:
        allowed_users = self.who_can_merge_pr()

        if username in allowed_users:
            return True

        return False

    def _get_collaborators_with_permission(self) -> dict:
        """
        Get all project collaborators in dictionary with permission association
        :return: List of usernames
        """
        collaborators = {}
        users = self.github_repo.get_collaborators()
        for user in users:
            permission = self.github_repo.get_collaborator_permission(user)
            collaborators[user.login] = permission
        return collaborators

    def get_issue_list(self, status: IssueStatus = IssueStatus.open) -> List[Issue]:
        issues = self.github_repo.get_issues(
            state=status.name, sort="updated", direction="desc"
        )
        try:
            return [self._issue_from_github_object(issue) for issue in issues]
        except UnknownObjectException:
            return []

    def get_issue_info(self, issue_id: int) -> Issue:
        issue = self.github_repo.get_issue(number=issue_id)
        return self._issue_from_github_object(issue)

    def _get_all_issue_comments(self, issue_id: int) -> List[IssueComment]:
        issue = self.github_repo.get_pull(number=issue_id)
        return [
            self._issuecomment_from_github_object(raw_comment)
            for raw_comment in issue.get_issue_comments()
        ]

    def issue_comment(self, issue_id: int, body: str) -> IssueComment:
        """
        Create comment on an issue.

        :param issue_id: int The ID of the issue
        :param body: str The text of the comment
        :return: IssueComment
        """
        github_issue = self.github_repo.get_issue(number=issue_id)
        comment = github_issue.create_comment(body)
        return self._issuecomment_from_github_object(comment)

    def create_issue(self, title: str, body: str) -> Issue:
        github_issue = self.github_repo.create_issue(title=title, body=body)
        return self._issue_from_github_object(github_issue)

    def issue_close(self, issue_id: int) -> Issue:
        issue = self.github_repo.get_issue(number=issue_id)
        issue.edit(state="closed")
        return issue

    def get_issue_labels(self, issue_id: int) -> List[GithubLabel]:
        """
        Get list of issue's labels.
        :issue_id: int
        :return: [GithubLabel]
        """
        issue = self.github_repo.get_issue(number=issue_id)
        return list(issue.get_labels())

    def add_issue_labels(self, issue_id, labels) -> None:
        """
        Add labels the the Issue.

        :param issue_id: int
        :param labels: [str]
        """
        issue = self.github_repo.get_issue(number=issue_id)
        for label in labels:
            issue.add_to_labels(label)

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List[PullRequest]:
        prs = self.github_repo.get_pulls(
            # Github API has no status 'merged', just 'closed'/'opened'/'all'
            state=status.name if status != PRStatus.merged else "closed",
            sort="updated",
            direction="desc",
        )

        if status == PRStatus.merged:
            prs = list(prs)  # Github PaginatedList into list()
            for pr in prs:
                if not pr.is_merged():  # parse merged PRs
                    prs.remove(pr)
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

    def get_sha_from_tag(self, tag_name: str) -> str:
        # TODO: This is ugly. Can we do it better?
        all_tags = self.github_repo.get_tags()
        for tag in all_tags:
            if tag.name == tag_name:
                return tag.commit.sha
        return ""

    def get_tag_from_tag_name(self, tag_name: str) -> Optional[GitTag]:
        all_tags = self.github_repo.get_tags()
        for tag in all_tags:
            if tag.name == tag_name:
                return GitTag(name=tag.name, commit_sha=tag.commit.sha)
        return None

    @if_readonly(return_function=GitProjectReadOnly.pr_create)
    def pr_create(
        self, title: str, body: str, target_branch: str, source_branch: str
    ) -> PullRequest:
        created_pr = self.github_repo.create_pull(
            title=title, body=body, base=target_branch, head=source_branch
        )
        return self._pr_from_github_object(created_pr)

    def update_pr_info(self, pr_id: int, title: str, description: str):
        """
        Update pull-request information.

        :param pr_id: int The ID of the pull request
        :param title: str The title of the pull request
        :param description str The description of the pull request
        :return: PullRequest
        """
        pr = self.github_repo.get_pull(number=pr_id)
        if not pr:
            raise GithubAPIException("PR was not found.")
        try:
            pr.edit(title=title, body=description)
            logger.info(f"PR updated: {pr.url}")
            return self._pr_from_github_object(pr)
        except Exception as ex:
            raise GithubAPIException("there was an error while updating the PR", ex)

    @if_readonly(
        return_function=GitProjectReadOnly.pr_comment,
        log_message="Create Comment to PR",
    )
    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
    ) -> PRComment:
        """
        Create comment on a pull request. If creating pull request review
        comment (bind to specific point in diff), all values need to be filled.

        :param pr_id: int The ID of the pull request
        :param body: str The text of the comment
        :param commit: str The SHA of the commit needing a comment.
        :param filename: str The relative path to the file that necessitates a comment
        :param row: int The position in the diff where you want to add a review comment
            see https://developer.github.com/v3/pulls/comments/#create-a-comment for more info
        :return: PRComment
        """
        github_pr = self.github_repo.get_pull(number=pr_id)
        if not any([commit, filename, row]):
            comment = github_pr.create_issue_comment(body)
        else:
            github_commit = self.github_repo.get_commit(commit)
            comment = github_pr.create_comment(body, github_commit, filename, row)
        return self._prcomment_from_github_object(comment)

    @if_readonly(
        return_function=GitProjectReadOnly.commit_comment,
        log_message="Create Comment to commit",
    )
    def commit_comment(
        self, commit: str, body: str, filename: str = None, row: int = None
    ) -> CommitComment:
        """
        Create comment on a commit.

        :param commit: str The SHA of the commit needing a comment.
        :param body: str The text of the comment
        :param filename: str The relative path to the file that necessitates a comment
        :param row: int Line index in the diff to comment on.
        :return: CommitComment
        """
        github_commit = self.github_repo.get_commit(commit)
        if filename and row:
            comment = github_commit.create_comment(
                body=body, position=row, path=filename
            )
        else:
            comment = github_commit.create_comment(body=body)
        return self._commitcomment_from_github_object(comment)

    def get_pr_labels(self, pr_id: int) -> List[GithubLabel]:
        """
        Get list of pr's labels.
        :pr_id: int
        :return: [GithubLabel]
        """
        pr = self.github_repo.get_pull(number=pr_id)
        return list(pr.get_labels())

    def add_pr_labels(self, pr_id, labels) -> None:
        """
        Add labels the the Pull Request.

        :param pr_id: int
        :param labels: [str]
        """
        pr = self.github_repo.get_pull(number=pr_id)
        for label in labels:
            pr.add_to_labels(label)

    @if_readonly(
        return_function=GitProjectReadOnly.set_commit_status,
        log_message="Create a status on a commit",
    )
    def set_commit_status(self, commit, state, target_url, description, context):
        """
        Create a status on a commit

        :param commit: The SHA of the commit.
        :param state: The state of the status.
        :param target_url: The target URL to associate with this status.
        :param description: A short description of the status
        :param context: A label to differentiate this status from the status of other systems.
        :return:
        """
        github_commit = self.github_repo.get_commit(commit)
        github_commit.create_status(state, target_url, description, context)
        return CommitFlag(commit, state, context)

    @if_readonly(return_function=GitProjectReadOnly.pr_close)
    def pr_close(self, pr_id: int) -> PullRequest:
        raise NotImplementedError

    @if_readonly(return_function=GitProjectReadOnly.pr_merge)
    def pr_merge(self, pr_id: int) -> PullRequest:
        closed_pr = self.github_repo.get_pull(number=pr_id).merge()
        return self._pr_from_github_object(closed_pr)

    def get_git_urls(self) -> Dict[str, str]:
        return {"git": self.github_repo.clone_url, "ssh": self.github_repo.ssh_url}

    @if_readonly(return_function=GitProjectReadOnly.fork_create)
    def fork_create(self) -> "GithubProject":
        """
        Fork this project using the authenticated user.
        This may raise an exception if the fork already exists.

        :return: fork GithubProject instance
        """
        gh_user = self.github_instance.get_user()
        fork = gh_user.create_fork(self.github_repo)
        return GithubProject("", self.service, "", github_repo=fork)

    def change_token(self, new_token: str):
        raise NotImplementedError

    def get_file_content(self, path: str, ref="master") -> str:
        try:
            return self.github_repo.get_contents(
                path=path, ref=ref
            ).decoded_content.decode()
        except UnknownObjectException as ex:
            raise FileNotFoundError(f"File '{path}' on {ref} not found", ex)

    @staticmethod
    def _issue_from_github_object(github_issue: GithubIssue) -> Issue:
        return Issue(
            title=github_issue.title,
            id=github_issue.number,
            status=IssueStatus[github_issue.state],
            url=github_issue.html_url,
            description=github_issue.body,
            author=github_issue.user.login,
            created=github_issue.created_at,
        )

    @staticmethod
    def _pr_from_github_object(github_pr: GithubPullRequest) -> PullRequest:
        return PullRequest(
            title=github_pr.title,
            id=github_pr.number,
            status=PRStatus.merged
            if github_pr.is_merged()
            else PRStatus[github_pr.state],
            url=github_pr.html_url,
            description=github_pr.body,
            author=github_pr.user.name,
            source_branch=github_pr.head.ref,
            target_branch=github_pr.base.ref,
            created=github_pr.created_at,
        )

    @staticmethod
    def _issuecomment_from_github_object(
        raw_comment: GithubIssueComment
    ) -> IssueComment:
        return IssueComment(
            comment=raw_comment.body,
            author=raw_comment.user.login,
            created=raw_comment.created_at,
            edited=raw_comment.updated_at,
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
    def _release_from_github_object(
        raw_release: GithubRelease, git_tag: GitTag
    ) -> Release:
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
            git_tag=git_tag,
        )

    @staticmethod
    def _commitcomment_from_github_object(
        raw_commitcoment: GithubCommitComment
    ) -> CommitComment:
        return CommitComment(
            comment=raw_commitcoment.body,
            author=raw_commitcoment.user.login,
            sha=raw_commitcoment.commit_id,
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
        return self._release_from_github_object(
            raw_release=release, git_tag=self.get_tag_from_tag_name(release.tag_name)
        )

    def get_latest_release(self) -> Release:
        release = self.github_repo.get_latest_release()
        return self._release_from_github_object(
            raw_release=release, git_tag=self.get_tag_from_tag_name(release.tag_name)
        )

    def get_releases(self) -> List[Release]:
        releases = self.github_repo.get_releases()
        return [
            self._release_from_github_object(
                raw_release=release,
                git_tag=self.get_tag_from_tag_name(release.tag_name),
            )
            for release in releases
        ]

    def create_release(self, tag: str, name: str, message: str) -> Release:
        created_release = self.github_repo.create_git_release(
            tag=tag, name=name, message=message
        )
        return self.get_release(created_release.id)

    def get_forks(self) -> List["GithubProject"]:
        """
        Get forks of the project.

        :return: [PagureProject]
        """
        fork_objects = [
            GithubProject(
                repo=fork.name,
                namespace=fork.owner.login,
                github_repo=fork,
                service=self.service,
                read_only=self.read_only,
            )
            for fork in self.github_repo.get_forks()
        ]
        return fork_objects


class GithubUser(BaseGitUser):
    service: GithubService

    def __init__(self, service: GithubService) -> None:
        super().__init__(service=service)

    def __str__(self) -> str:
        return f'GithubUser(username="{self.get_username()}")'

    @property
    def _github_user(self):
        return self.service.github.get_user()

    def get_username(self) -> str:
        return self.service.github.get_user().login

    def get_projects(self) -> List["GithubProject"]:
        raw_repos = self._github_user.get_repos(affiliation="owner")
        return [
            GithubProject(
                repo=repo.name,
                namespace=repo.owner.login,
                github_repo=repo,
                service=self.service,
            )
            for repo in raw_repos
        ]

    def get_forks(self) -> List["GithubProject"]:
        forks = [project for project in self.get_projects() if project.github_repo.fork]
        return forks

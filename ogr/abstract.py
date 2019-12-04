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
from enum import Enum, IntEnum
from typing import Optional, Match, List, Dict, Set, TypeVar, Any, Sequence, Union
from urllib.request import urlopen
import warnings

from ogr.deprecation import deprecate_and_set_removal
from ogr.exceptions import OgrException
from ogr.parsing import parse_git_repo

AnyComment = TypeVar("AnyComment", bound="Comment")


class Comment:
    def __init__(
        self,
        raw_comment: Optional[Any] = None,
        parent: Optional[Any] = None,
        body: Optional[str] = None,
        author: Optional[str] = None,
        created: Optional[datetime.datetime] = None,
        edited: Optional[datetime.datetime] = None,
    ) -> None:
        if raw_comment:
            self._from_raw_comment(raw_comment)
        elif body and author:
            self._body = body
            self._author = author
            self._created = created
            self._edited = edited
        else:
            raise ValueError("cannot construct comment without body and author")

        self._parent = parent

    def __str__(self) -> str:
        body = f"{self.body[:10]}..." if self.body is not None else "None"
        return (
            f"Comment("
            f"comment='{body}', "
            f"author='{self.author}', "
            f"created='{self.created}', "
            f"edited='{self.edited}')"
        )

    def _from_raw_comment(self, raw_comment: Any) -> None:
        """Constructs Comment object from raw_comment given from API."""
        raise NotImplementedError()

    @property
    def comment(self):
        warnings.warn(
            "Using deprecated property, that will be removed in 0.14.0"
            " (or 1.0.0 if it comes sooner). Please use body. "
        )
        return self.body

    @property
    def body(self) -> str:
        return self._body

    @body.setter
    def body(self, new_body: str) -> None:
        self._body = new_body

    @property
    def author(self) -> str:
        return self._author

    @property
    def created(self) -> datetime.datetime:
        return self._created

    @property
    def edited(self) -> datetime.datetime:
        return self._edited


class IssueComment(Comment):
    @property
    def issue(self) -> "Issue":
        return self._parent

    def __str__(self) -> str:
        return "Issue" + super().__str__()


class PRComment(Comment):
    @property
    def pull_request(self) -> "PullRequest":
        return self._parent

    def __str__(self) -> str:
        return "PR" + super().__str__()


class IssueStatus(IntEnum):
    opened = 1
    open = opened
    closed = 2
    all = 3


class Issue:
    def __init__(self, raw_issue: Any, project: "GitProject") -> None:
        self._raw_issue = raw_issue
        self.project = project

    @property
    def title(self) -> str:
        raise NotImplementedError()

    @property
    def id(self) -> int:
        raise NotImplementedError()

    @property
    def status(self) -> IssueStatus:
        raise NotImplementedError()

    @property
    def url(self) -> str:
        raise NotImplementedError()

    @property
    def description(self) -> str:
        raise NotImplementedError()

    @property
    def author(self) -> str:
        raise NotImplementedError()

    @property
    def created(self) -> datetime.datetime:
        raise NotImplementedError()

    @property
    def labels(self) -> List:
        raise NotImplementedError()

    def __str__(self) -> str:
        description = (
            f"{self.description[:10]}..." if self.description is not None else "None"
        )
        return (
            f"Issue("
            f"title='{self.title}', "
            f"id={self.id}, "
            f"status='{self.status.name}', "
            f"url='{self.url}', "
            f"description='{description}', "
            f"author='{self.author}', "
            f"created='{self.created}')"
        )

    @staticmethod
    def create(project: Any, title: str, body: str) -> "Issue":
        """
        Open new Issue.

        :param project: Any
        :param title: str
        :param body: str
        :return: Issue
        """
        raise NotImplementedError()

    @staticmethod
    def get(project: Any, id: int) -> "Issue":
        """
        Get issue.

        :param project: Any
        :param id: int
        :return: Issue
        """
        raise NotImplementedError()

    @staticmethod
    def get_list(project: Any, status: IssueStatus = IssueStatus.open) -> List["Issue"]:
        """
        List of issues.

        :param project: Any
        :param status: IssueStatus enum
        :return: [Issue]
        """
        raise NotImplementedError()

    def _get_all_comments(self) -> List[IssueComment]:
        """
        Get list of issue comments.

        :return: [IssueComment]
        """
        raise NotImplementedError()

    def get_comments(
        self, filter_regex: str = None, reverse: bool = False, author: str = None
    ) -> List[IssueComment]:
        """
        Get list of issue comments.

        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :param author: filter comments by author
        :return: [IssueComment]
        """
        raise NotImplementedError()

    def can_close(self, username: str) -> bool:
        """
        Check if user have permissions to modify an Issue.

        :param username: str
        :return: true if user can close issue, false otherwise
        """
        raise NotImplementedError()

    def comment(self, body: str) -> IssueComment:
        """
        Add new comment to the issue.

        :param body: str
        :return: IssueComment
        """
        raise NotImplementedError()

    def close(self) -> "Issue":
        """
        Close an issue.

        :return: Issue
        """
        raise NotImplementedError()

    def add_label(self, *labels: str) -> None:
        """
        Add labels the the Issue.

        :param labels: [str]
        """
        raise NotImplementedError()


class PRStatus(IntEnum):
    opened = 1
    open = opened
    closed = 2
    merged = 3
    all = 4


class PullRequest:
    @deprecate_and_set_removal(
        since="0.9.0",
        remove_in="0.14.0 (or 1.0.0 if it comes sooner)",
        message="Use PullRequestReadOnly from ogr.read_only",
    )
    def __init__(
        self,
        title: str,
        description: str,
        target_branch: str,
        source_branch: str,
        id: int,
        status: PRStatus,
        url: str,
        author: str,
        created: datetime.datetime,
    ) -> None:
        self._title = title
        self._description = description
        self._target_branch = target_branch
        self._source_branch = source_branch
        self._id = id
        self._status = PRStatus.open
        self._url = url
        self._author = author
        self._created = created

    @property
    def title(self) -> str:
        return self._title

    @property
    def id(self) -> int:
        return self._id

    @property
    def status(self) -> PRStatus:
        return self._status

    @property
    def url(self) -> str:
        return self._url

    @property
    def description(self) -> str:
        return self._description

    @property
    def author(self) -> str:
        return self._author

    @property
    def source_branch(self) -> str:
        return self._source_branch

    @property
    def target_branch(self) -> str:
        return self._target_branch

    @property
    def created(self) -> datetime.datetime:
        return self._created

    @property
    def labels(self) -> List[Any]:
        raise NotImplementedError()

    def __str__(self) -> str:
        description = (
            f"{self.description[:10]}..." if self.description is not None else "None"
        )
        return (
            f"PullRequest("
            f"title='{self.title}', "
            f"id={self.id}, "
            f"status='{self.status.name}', "
            f"url='{self.url}', "
            f"description='{description}', "
            f"author='{self.author}', "
            f"source_branch='{self.source_branch}', "
            f"target_branch='{self.target_branch}', "
            f"created='{self.created}'), "
        )

    @staticmethod
    def create(
        project: Any,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        """
        Create a new pull request.

        :param project: Any
        :param title: str
        :param body: str
        :param target_branch: str
        :param source_branch: str
        :param fork_username: str The username/namespace of the forked repository.
        :return: PullRequest
        """
        raise NotImplementedError()

    @staticmethod
    def get(project: Any, id: int) -> "PullRequest":
        """
        Get pull request

        :param project: Any
        :param id: int
        :return: PullRequest
        """
        raise NotImplementedError()

    @staticmethod
    def get_list(project: Any, status: PRStatus = PRStatus.open) -> List["PullRequest"]:
        """
        List of pull requests

        :param project: Any
        :param status: PRStatus enum
        :return: [PullRequest]
        """
        raise NotImplementedError()

    def update_info(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> "PullRequest":
        """
        Update pull-request information.

        :param title: str The title of the pull request
        :param description str The description of the pull request
        :return: PullRequest
        """
        raise NotImplementedError()

    def _get_all_comments(self) -> List[PRComment]:
        """
        Get list of pull-request comments.

        :param pr_id: int
        :return: [PRComment]
        """
        raise NotImplementedError()

    def get_comments(
        self,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> List["PRComment"]:
        """
        Get list of pull-request comments.

        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :param author: filter comments by author
        :return: [PRComment]
        """
        raise NotImplementedError()

    def get_all_commits(self) -> List[str]:
        """
        Return list of pull-request commits (sha).

        :return: [str]
        """
        raise NotImplementedError()

    def search(
        self, filter_regex: str, reverse: bool = False, description: bool = True
    ) -> Optional[Match[str]]:
        """
        Find match in pull-request description or comments.

        :param description: bool (search in description?)
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :return: re.Match or None
        """
        raise NotImplementedError()

    def comment(
        self,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
        """
        Add new comment to the pull request.

        :param body: str
        :param commit: str
        :param filename: str
        :param row: int
        :return: PRComment
        """
        raise NotImplementedError()

    def close(self) -> "PullRequest":
        """
        Close the pull-request.

        :return:  PullRequest
        """
        raise NotImplementedError()

    def merge(self) -> "PullRequest":
        """
        Merge the pull request.

        :return: PullRequest
        """
        raise NotImplementedError()

    def add_label(self, *labels: str) -> None:
        """
        Add labels the the Pull Request.

        :param pr_id: int
        :param *labels: str
        """
        raise NotImplementedError()

    def get_statuses(self) -> List["CommitFlag"]:
        """
        Returns statuses for latest commit on pull request.

        :return: [CommitFlag]
        """
        raise NotImplementedError()


class CommitStatus(Enum):
    pending = 1
    success = 2
    failure = 3
    error = 4
    canceled = 5
    running = 6


class CommitFlag:
    _states: Dict[str, CommitStatus] = dict()

    def __init__(
        self,
        raw_commit_flag: Optional[Any] = None,
        project: Optional["GitProject"] = None,
        commit: Optional[str] = None,
        state: Optional[CommitStatus] = None,
        context: Optional[str] = None,
        comment: Optional[str] = None,
        uid: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        if commit and state and context:
            self.commit = commit
            self.state = state
            self.context = context
            self.comment = comment
            self.url = url
        else:
            self._raw_commit_flag = raw_commit_flag
            self._from_raw_commit_flag()
        self.uid = uid
        self.project = project

    def __str__(self) -> str:
        return (
            f"CommitFlag("
            f"commit='{self.commit}', "
            f"state='{self.state.name}', "
            f"context='{self.context}', "
            f"uid='{self.uid}',"
            f"comment='{self.comment}',"
            f"url='{self.url}')"
        )

    def _state_from_str(self, state: str) -> CommitStatus:
        if state not in self._states:
            raise ValueError("non-existing status")
        return self._states[state]

    def _from_raw_commit_flag(self) -> None:
        raise NotImplementedError()

    @staticmethod
    def get(project: Any, commit: str) -> List["CommitFlag"]:
        raise NotImplementedError()

    @staticmethod
    def set(
        project: Any,
        commit: str,
        state: CommitStatus,
        target_url: str,
        description: str,
        context: str,
    ) -> "CommitFlag":
        raise NotImplementedError()


class CommitComment:
    def __init__(self, sha: str, comment: str, author: str) -> None:
        self.sha = sha
        self.comment = comment
        self.author = author


class GitTag:
    def __init__(self, name: str, commit_sha: str) -> None:
        self.name = name
        self.commit_sha = commit_sha

    def __str__(self) -> str:
        return f"GitTag(name={self.name}, commit_sha={self.commit_sha})"


class Release:
    def __init__(
        self,
        tag_name: str,
        url: Optional[str],
        created_at: str,
        tarball_url: str,
        git_tag: GitTag,
        project: "GitProject",
    ) -> None:
        self.tag_name = tag_name
        self.url = url
        self.created_at = created_at
        self.tarball_url = tarball_url
        self.git_tag = git_tag
        self.project = project

    @property
    def title(self) -> str:
        raise NotImplementedError()

    @property
    def body(self) -> str:
        raise NotImplementedError()

    def save_archive(self, filename: str) -> None:
        response = urlopen(self.tarball_url)
        data = response.read()

        with open(filename, "wb") as file:
            file.write(data)

    def __str__(self) -> str:
        return (
            f"Release("
            f"title='{self.title}', "
            f"body='{self.body}', "
            f"tag_name='{self.tag_name}', "
            f"url='{self.url}',"
            f"created_at='{self.created_at}',"
            f"tarball_url='{self.tarball_url}')"
        )

    def edit_release(self, name: str, message: str) -> None:
        """
        Edit name and message of a release.

        :param name: str
        :param message: str
        """
        raise NotImplementedError()


class GitService:
    instance_url: Optional[str] = None

    def __init__(self, **_: Any) -> None:
        pass

    def get_project(self, **kwargs: Any) -> "GitProject":
        """
        Get the GitProject instance

        :param namespace: str
        :param user: str
        :param repo: str
        :return: GitProject
        """
        raise NotImplementedError

    def get_project_from_url(self, url: str) -> "GitProject":
        repo_url = parse_git_repo(potential_url=url)
        if not repo_url:
            raise OgrException(f"Failed to find repository for url: {url}")
        project = self.get_project(repo=repo_url.repo, namespace=repo_url.namespace)
        return project

    @property
    def user(self) -> "GitUser":
        """
        GitUser instance for used token.

        :return: GitUser
        """
        raise NotImplementedError

    def change_token(self, new_token: str) -> None:
        """
        Change an API token.

        Only for this instance and newly created Projects via get_project.
        """
        raise NotImplementedError

    def project_create(
        self, repo: str, namespace: Optional[str] = None
    ) -> "GitProject":
        """
        Create a new project.

        :param repo: str
        :param namespace: Optional[str]
        :return: GitProject
        """
        raise NotImplementedError()


class GitProject:
    def __init__(self, repo: str, service: GitService, namespace: str) -> None:
        """
        :param repo: name of the project
        :param service: GitService instance
        :param namespace:   github: username or org name
                            gitlab: username or org name
                            pagure: namespace (e.g. "rpms")
                                for forks: "fork/{username}/{namespace}"
        """
        self.service = service
        self.repo = repo
        self.namespace = namespace

    def is_forked(self) -> bool:
        """
        Is this repo forked by the authenticated user?

        :return: if yes, return True
        """
        raise NotImplementedError()

    @property
    def is_fork(self) -> bool:
        """True if the project is a fork."""
        raise NotImplementedError()

    @property
    def full_repo_name(self) -> str:
        """
        Get repo name with namespace
        e.g. 'rpms/python-docker-py'

        :return: str
        """
        raise NotImplementedError()

    @property
    def parent(self) -> Optional["GitProject"]:
        """
        Return parent project if this project is a fork, otherwise return None
        """
        raise NotImplementedError()

    def get_branches(self) -> List[str]:
        """
        List of project branches.

        :return: [str]
        """
        raise NotImplementedError()

    def get_description(self) -> str:
        """
        Project description.

        :return: str
        """
        raise NotImplementedError()

    def get_fork(self, create: bool = True) -> Optional["GitProject"]:
        """
        Provide GitProject instance of a fork of this project.

        Returns None if this is a fork.

        :param create: create a fork if it doesn't exist
        :return: instance of GitProject or None
        """
        raise NotImplementedError()

    def get_owners(self) -> List[str]:
        """
        Get all project owners
        :return: List of usernames
        """
        raise NotImplementedError()

    def who_can_close_issue(self) -> Set[str]:
        """
        Get all usernames who have permissions to modify an Issue
        :return: Set of usernames
        """
        raise NotImplementedError()

    def who_can_merge_pr(self) -> Set[str]:
        """
        Get all usernames who have permissions to modify a PR
        :return: Set of usernames
        """
        raise NotImplementedError()

    def can_close_issue(self, username: str, issue: Issue) -> bool:
        """
        Check if user have permissions to modify an Issue
        :param username: str
        :param issue: Issue
        :return: true if user can close issue, false otherwise
        """
        raise NotImplementedError()

    def can_merge_pr(self, username: str) -> bool:
        """
        Check if user have permissions to modify an Pr
        :param username: str
        :return: true if user can close PR, false otherwise
        """
        raise NotImplementedError()

    def get_issue_list(self, status: IssueStatus = IssueStatus.open) -> List["Issue"]:
        """
        List of issues (dics)

        :param status: IssueStatus enum
        :return: [Issue]
        """
        raise NotImplementedError()

    def get_issue(self, issue_id: int) -> "Issue":
        """
        Get issue

        :param issue_id: int
        :return: Issue
        """
        raise NotImplementedError()

    def get_issue_info(self, issue_id: int) -> "Issue":
        """
        Get issue info

        :param issue_id: int
        :return: Issue
        """
        raise NotImplementedError()

    def _get_all_issue_comments(self, issue_id: int) -> List["IssueComment"]:
        """
        Get list of issue comments.

        :param issue_id: int
        :return: [IssueComment]
        """
        raise NotImplementedError()

    def get_issue_comments(
        self,
        issue_id: int,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> List["IssueComment"]:
        """
        Get list of Issue comments.

        :param issue_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :param author: filter comments by author
        :return: [IssueComment]
        """
        raise NotImplementedError()

    def issue_comment(self, issue_id: int, body: str) -> "IssueComment":
        """
        Add new comment to the issue.

        :param issue_id: int
        :param body: str
        :return: IssueComment
        """
        raise NotImplementedError()

    def create_issue(self, title: str, body: str) -> Issue:
        """
        Open new Issue.

        :param title: str
        :param body: str
        :return: Issue
        """
        raise NotImplementedError()

    def issue_close(self, issue_id: int) -> Issue:
        """
        Close an issue

        :param issue_id: int
        :return: Issue
        """
        raise NotImplementedError()

    def get_issue_labels(self, issue_id: int) -> List[Any]:
        """
        Get list of issue's labels.

        :issue_id: int
        :return: [GithubLabel]
        """
        raise NotImplementedError()

    def add_issue_labels(self, issue_id: int, labels: List[str]) -> None:
        """
        Add labels the the Issue.

        :param issue_id: int
        :param labels: [str]
        """
        raise NotImplementedError()

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List["PullRequest"]:
        """
        List of pull requests (dics)

        :param status: PRStatus enum
        :return: [PullRequest]
        """
        raise NotImplementedError()

    def get_pr(self, pr_id: int) -> "PullRequest":
        """
        Get pull request

        :param pr_id: int
        :return: PullRequest
        """
        raise NotImplementedError()

    def get_pr_info(self, pr_id: int) -> "PullRequest":
        """
        Get pull request info

        :param pr_id: int
        :return: PullRequest
        """
        raise NotImplementedError()

    def update_pr_info(
        self, pr_id: int, title: Optional[str] = None, description: Optional[str] = None
    ) -> PullRequest:
        """
        Update pull-request information.

        :param pr_id: int The ID of the pull request
        :param title: str The title of the pull request
        :param description str The description of the pull request
        :return: PullRequest
        """
        raise NotImplementedError()

    def get_tags(self) -> List["GitTag"]:
        """
        Return list of tags.

        :return: [GitTags]
        """
        raise NotImplementedError()

    def get_sha_from_tag(self, tag_name: str) -> str:
        """
        Search tag name in existing tags and return sha

        :param tag_name: str
        :return: str
        """
        raise NotImplementedError()

    def get_release(
        self,
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> Release:
        """
        Get a single release

        :param identifier: int
        :param name: str
        :param tag_name: str
        :return: Release
        """
        raise NotImplementedError()

    def get_latest_release(self) -> Release:
        """
        Get a latest release

        :return: Release
        """
        raise NotImplementedError()

    def get_releases(self) -> List[Release]:
        """
        Return list of releases

        :return: [Release]
        """
        raise NotImplementedError()

    def _get_all_pr_comments(self, pr_id: int) -> List[PRComment]:
        """
        Get list of pull-request comments.

        :param pr_id: int
        :return: [PRComment]
        """
        raise NotImplementedError()

    def get_pr_comments(
        self,
        pr_id: int,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> List["PRComment"]:
        """
        Get list of pull-request comments.

        :param pr_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :param author: filter comments by author
        :return: [PRComment]
        """
        raise NotImplementedError()

    def get_all_pr_commits(self, pr_id: int) -> List[str]:
        """
        Return list of pull-request commits (sha).

        :param pr_id: int
        :return: [str]
        """
        raise NotImplementedError()

    def search_in_pr(
        self,
        pr_id: int,
        filter_regex: str,
        reverse: bool = False,
        description: bool = True,
    ) -> Optional[Match[str]]:
        """
        Find match in pull-request description or comments.

        :param description: bool (search in description?)
        :param pr_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :return: re.Match or None
        """
        raise NotImplementedError()

    def pr_create(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        """
        Create a new pull request.

        :param title: str
        :param body: str
        :param target_branch: str
        :param source_branch: str
        :param fork_username: str The username of forked repository
        :return: PullRequest
        """
        raise NotImplementedError()

    def create_pr(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: str = None,
    ) -> "PullRequest":
        """
        Create a new pull request.

        :param title: str
        :param body: str
        :param target_branch: str
        :param source_branch: str
        :param fork_username: str The username of forked repository
        :return: PullRequest
        """
        raise NotImplementedError()

    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: Optional[str] = None,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "PRComment":
        """
        Add new comment to the pull request.

        :param pr_id: int
        :param body: str
        :param commit: str
        :param filename: str
        :param row: int
        :return: PRComment
        """
        raise NotImplementedError()

    def commit_comment(
        self,
        commit: str,
        body: str,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "CommitComment":
        """
        Add new comment to a commit.

        :param commit: str
        :param body: str
        :param filename: str
        :param row: int
        :return: CommitComment
        """
        raise NotImplementedError()

    def set_commit_status(
        self,
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
    ) -> "CommitFlag":
        """
        Create a status on a commit

        :param commit: The SHA of the commit.
        :param state: The state of the status.
        :param target_url: The target URL to associate with this status.
        :param description: A short description of the status
        :param context: A label to differentiate this status from the status of other systems.
        :return:
        """
        raise NotImplementedError()

    def get_commit_statuses(self, commit: str) -> List[CommitFlag]:
        """
        Get status of the commit.

        :param commit: str
        :return: [CommitFlag]
        """
        raise NotImplementedError()

    def pr_close(self, pr_id: int) -> "PullRequest":
        """
        Close the pull-request.

        :param pr_id: int
        :return:  PullRequest
        """
        raise NotImplementedError()

    def pr_merge(self, pr_id: int) -> "PullRequest":
        """
        Merge the pull request.

        :param pr_id: int
        :return: PullRequest
        """
        raise NotImplementedError()

    def get_pr_labels(self, pr_id: int) -> List[Any]:
        """
        Get list of pr's labels.
        :pr_id: int
        :return: [GithubLabel]
        """
        raise NotImplementedError()

    def add_pr_labels(self, pr_id: int, labels: List[str]) -> None:
        """
        Add labels the the Pull Request.

        :param pr_id: int
        :param labels: [str]
        """
        raise NotImplementedError()

    def get_git_urls(self) -> Dict[str, str]:
        raise NotImplementedError()

    def fork_create(self) -> "GitProject":
        """
        Fork this project using the authenticated user.
        This may raise an exception if the fork already exists.

        :return: fork GitProject instance
        """
        raise NotImplementedError()

    def change_token(self, new_token: str) -> None:
        """
        Change an API token.

        Only for this instance.
        """
        raise NotImplementedError

    def get_file_content(self, path: str, ref: str = "master") -> str:
        """
        Get a content of the file in the repo.

        :param ref: branch or commit (defaults to master)
        :param path: str
        :return: str or FileNotFoundError if there is no such file
        """
        raise NotImplementedError

    def get_forks(self) -> Sequence["GitProject"]:
        """
        Get forks of the project.

        :return: [GitProject]
        """
        raise NotImplementedError

    def get_web_url(self) -> str:
        """
        Get web URL of the project.

        :return: str
        """
        raise NotImplementedError


class GitUser:
    def __init__(self, service: GitService) -> None:
        self.service = service

    def get_username(self) -> str:
        raise NotImplementedError()

    def get_email(self) -> str:
        raise NotImplementedError()

    def get_projects(self) -> Sequence["GitProject"]:
        raise NotImplementedError

    def get_forks(self) -> Sequence["GitProject"]:
        raise NotImplementedError

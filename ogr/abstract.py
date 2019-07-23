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
from enum import IntEnum
from typing import Optional, Match, List, Dict, Set
from urllib.request import urlopen

from ogr.parsing import parse_git_repo


class IssueStatus(IntEnum):
    open = 1
    closed = 2
    all = 3


class Issue:
    def __init__(
        self,
        title: str,
        id: int,
        status: IssueStatus,
        url: str,
        description: str,
        author: str,
        created: datetime.datetime,
    ) -> None:
        self.title = title
        self.id = id
        self.status = status
        self.url = url
        self.description = description
        self.author = author
        self.created = created

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


class IssueComment:
    def __init__(
        self,
        comment: str,
        author: str,
        created: Optional[datetime.datetime] = None,
        edited: Optional[datetime.datetime] = None,
    ) -> None:
        self.comment = comment
        self.author = author
        self.created = created
        self.edited = edited

    def __str__(self) -> str:
        comment = f"{self.comment[:10]}..." if self.comment is not None else "None"
        return (
            f"IssueComment("
            f"comment='{comment}', "
            f"author='{self.author}', "
            f"created='{self.created}', "
            f"edited='{self.edited}')"
        )


class PRStatus(IntEnum):
    open = 1
    closed = 2
    merged = 3
    all = 4


class PullRequest:
    def __init__(
        self,
        title: str,
        id: int,
        status: PRStatus,
        url: str,
        description: str,
        author: str,
        source_branch: str,
        target_branch: str,
        created: datetime.datetime,
    ) -> None:
        self.title = title
        self.id = id
        self.status = status
        self.url = url
        self.description = description
        self.author = author
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.created = created

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
            f"created='{self.created}')"
        )


class PRComment:
    def __init__(
        self,
        comment: str,
        author: str,
        created: Optional[datetime.datetime] = None,
        edited: Optional[datetime.datetime] = None,
    ) -> None:
        self.comment = comment
        self.author = author
        self.created = created
        self.edited = edited

    def __str__(self) -> str:
        comment = f"{self.comment[:10]}..." if self.comment is not None else "None"
        return (
            f"PRComment("
            f"comment='{comment}', "
            f"author='{self.author}', "
            f"created='{self.created}', "
            f"edited='{self.edited}')"
        )


class CommitFlag:
    def __init__(
        self,
        commit: str,
        state: str,
        context: str,
        comment: str = None,
        uid: str = None,
        url: str = None,
    ):
        self.commit = commit
        self.state = state  # Should be enum
        self.context = context
        self.uid = uid
        self.comment = comment
        self.url = url

    def __str__(self) -> str:
        return (
            f"CommitFlag("
            f"commit='{self.commit}', "
            f"state='{self.state}', "
            f"context='{self.context}', "
            f"uid='{self.uid}',"
            f"comment='{self.comment}',"
            f"url='{self.url}')"
        )


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
        title: str,
        body: str,
        tag_name: str,
        url: str,
        created_at: str,
        tarball_url: str,
        git_tag: GitTag,
    ) -> None:
        self.title = title
        self.body = body
        self.tag_name = tag_name
        self.url = url
        self.created_at = created_at
        self.tarball_url = tarball_url
        self.git_tag = git_tag

    def save_archive(self, filename):
        response = urlopen(self.tarball_url)
        data = response.read()

        file = open(filename, "w")
        file.write(data)
        file.close()

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


class GitService:
    instance_url: Optional[str] = None

    def __init__(self, **_):
        pass

    @classmethod
    def create_from_remote_url(cls, remote_url) -> "GitService":
        """
        Create instance of service from provided remote_url.

        :param remote_url: str
        :return: GitService
        """
        raise NotImplementedError()

    def get_project(self, **kwargs) -> "GitProject":
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
        return f"{self.namespace}/{self.repo}"

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

    def can_merge_pr(self, username) -> bool:
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
        self, issue_id, filter_regex: str = None, reverse: bool = False
    ) -> List["IssueComment"]:
        """
        Get list of Issue comments.

        :param issue_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
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

    def get_issue_labels(self, issue_id: int) -> List:
        """
        Get list of issue's labels.

        :issue_id: int
        :return: [GithubLabel]
        """
        raise NotImplementedError()

    def add_issue_labels(self, issue_id, labels) -> None:
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

    def get_pr_info(self, pr_id: int) -> "PullRequest":
        """
        Get pull request info

        :param pr_id: int
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

    def get_release(self, identifier: int) -> Release:
        """
        Get a single release

        :param identifier:
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

    def _get_all_pr_comments(self, pr_id: int) -> List["PRComment"]:
        """
        Get list of pull-request comments.

        :param pr_id: int
        :return: [PRComment]
        """
        raise NotImplementedError()

    def get_pr_comments(
        self, pr_id, filter_regex: str = None, reverse: bool = False
    ) -> List["PRComment"]:
        """
        Get list of pull-request comments.

        :param pr_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :return: [PRComment]
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
        self, title: str, body: str, target_branch: str, source_branch: str
    ) -> "PullRequest":
        """
        Create a new pull request.

        :param title: str
        :param body: str
        :param target_branch: str
        :param source_branch: str
        :return: PullRequest
        """
        raise NotImplementedError()

    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
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
        self, commit: str, body: str, filename: str = None, row: int = None
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
        self, commit: str, state: str, target_url: str, description: str, context: str
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

    def get_pr_labels(self, pr_id: int) -> List:
        """
        Get list of pr's labels.
        :pr_id: int
        :return: [GithubLabel]
        """
        raise NotImplementedError()

    def add_pr_labels(self, pr_id, labels) -> None:
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

    def change_token(self, new_token: str):
        """
        Change an API token.

        Only for this instance.
        """
        raise NotImplementedError

    def get_file_content(self, path: str, ref="master") -> str:
        """
        Get a content of the file in the repo.

        :param ref: branch or commit (defaults to master)
        :param path: str
        :return: str or FileNotFoundError if there is no such file
        """
        raise NotImplementedError

    def get_forks(self):
        """
        Get forks of the project.

        :return: [GitProject]
        """
        raise NotImplementedError


class GitUser:
    def __init__(self, service: GitService) -> None:
        self.service = service

    def get_username(self) -> str:
        raise NotImplementedError()

    def get_projects(self):
        raise NotImplementedError

    def get_forks(self):
        raise NotImplementedError

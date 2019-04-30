import datetime
from enum import IntEnum
from typing import Optional, Match, List, Dict
from urllib.request import urlopen


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


class PRComment:
    def __init__(
        self,
        comment: str,
        author: str,
        created: datetime.datetime,
        edited: datetime.datetime,
    ) -> None:
        self.comment = comment
        self.author = author
        self.created = created
        self.edited = edited


class CommitStatus:
    def __init__(self, commit: str, state: str, context: str):
        self.commit = commit
        self.state = state
        self.context = context


class CommitComment:
    def __init__(self, sha: str, comment: str, author: str) -> None:
        self.sha = sha
        self.comment = comment
        self.author = author


class Release:
    def __init__(
        self,
        title: str,
        body: str,
        tag_name: str,
        url: str,
        created_at: str,
        tarball_url: str,
    ) -> None:
        self.title = title
        self.body = body
        self.tag_name = tag_name
        self.url = url
        self.created_at = created_at
        self.tarball_url = tarball_url

    def save_archive(self, filename):
        response = urlopen(self.tarball_url)
        data = response.read()

        file = open(filename, "w")
        file.write(data)
        file.close()


class GitService:
    def __init__(self):
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

    def get_sha_from_tag(self, tag_name: str) -> str:
        """
        Search tag name in existing tags and return sha

        :param tag_name: str
        :return: str
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
    ) -> "CommitStatus":
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


class GitUser:
    def __init__(self, service: GitService) -> None:
        self.service = service

    def get_username(self) -> str:
        raise NotImplementedError()

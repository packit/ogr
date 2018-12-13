import datetime
from dataclasses import dataclass

from ogr.utils import PRStatus


class GitService:
    def __init__(self):
        pass

    @classmethod
    def create_from_remote_url(cls, remote_url):
        """
        Create instance of service from provided remote_url.

        :param remote_url: str
        :return: GitService
        """
        raise NotImplementedError()

    def get_project(self, namespace=None, user=None, repo=None):
        """
        Get the GitProject instance

        :param namespace: str
        :param user: str
        :param repo: str
        :return: GitProject
        """
        raise NotImplementedError

    @property
    def user(self):
        """
        GitUser instance for used token.

        :return: GitUser
        """
        raise NotImplementedError


class GitProject:
    def get_branches(self):
        """
        List of project branches.

        :return: [str]
        """
        raise NotImplementedError()

    def get_description(self):
        """
        Project description.

        :return: str
        """
        raise NotImplementedError()

    def pr_create(self, title, body, target_branch, current_branch):
        """
        Create a new pull request.

        :param title: str
        :param body: str
        :param target_branch: str
        :param current_branch: str
        :return: PullRequest
        """
        raise NotImplementedError()

    def get_pr_list(self, status=PRStatus.open):
        """
        List of pull requests (dics)

        :param status: PRStatus enum
        :return: [{str: str}]
        """
        raise NotImplementedError()

    def get_pr_info(self, pr_id):
        """
        Get pull request info

        :param pr_id: int
        :return: PullRequest
        """
        raise NotImplementedError()

    def get_pr_comments(self, pr_id):
        """
        Get list of pull-request comments.

        :param pr_id: int
        :return: [PRComment]
        """
        raise NotImplementedError()

    def pr_comment(self, pr_id, body, commit=None, filename=None, row=None):
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

    def pr_close(self, pr_id):
        """
        Close the pull-request.

        :param pr_id: int
        :return:  PullRequest
        """
        raise NotImplementedError()

    def pr_merge(self, pr_id):
        """
        Merge the pull request.

        :param pr_id: int
        :return: PullRequest
        """
        raise NotImplementedError()

    @property
    def fork(self):
        """
        GitProject instance of the fork if the fork exists, else None

        :return: GitProject or None
        """
        raise NotImplementedError()

    @property
    def is_forked(self):
        """
        True, if the project is forked by the user.

        :return: Bool
        """
        raise NotImplementedError()

    def fork_create(self):
        """
        Create a fork of the project.

        :return: GitProject
        """
        raise NotImplementedError()


class GitUser:
    @property
    def username(self):
        raise NotImplementedError()


@dataclass
class PullRequest:
    title: str
    id: int
    status: PRStatus
    url: str
    description: str
    author: str
    source_branch: str
    target_branch: str
    created: datetime.datetime


@dataclass
class PRComment:
    comment: str
    author: str
    created: datetime.datetime
    edited: datetime.datetime

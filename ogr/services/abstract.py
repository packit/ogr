import datetime
import re
from dataclasses import dataclass

import six

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
    def __init__(self, repo, namespace, service):
        """
        :param repo: name of the project
        :param namespace:   github: username or org name
                            gitlab: username or org name
                            pagure: namespace (e.g. "rpms")
                                for forks: "fork/{username}/{namespace}"
        :param service: GitService instance
        """
        self.service = service
        self.repo = repo
        self.namespace = namespace

    def is_forked(self):
        """
        True, if the project is forked by the user.

        :return: Bool
        """
        raise NotImplementedError()

    @property
    def is_fork(self):
        """True if the project is a fork."""
        raise NotImplementedError()

    @property
    def full_repo_name(self):
        """
        Get repo name with namespace
        e.g. 'rpms/python-docker-py'

        :return: str
        """
        return f"{self.namespace}/{self.repo}"

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

    def get_fork(self):
        """
        GitProject instance of the fork if the fork exists, else None

        :return: GitProject or None
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

    def _get_all_pr_comments(self, pr_id):
        """
        Get list of pull-request comments.

        :param pr_id: int
        :return: [PRComment]
        """
        raise NotImplementedError()

    def get_pr_comments(self, pr_id, filter_regex=None, reverse=False):
        """
        Get list of pull-request comments.

        :param pr_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :return: [PRComment]
        """
        all_comments = self._get_all_pr_comments(pr_id=pr_id)
        if reverse:
            all_comments.reverse()
        if filter_regex:
            pattern = re.compile(filter_regex)
            all_comments = list(
                filter(lambda comment: bool(pattern.search(comment.comment)), all_comments)
            )
        return all_comments

    def search_in_pr(self, pr_id, filter_regex, reverse=False, description=True):
        """
        Find match in pull-request description or comments.

        :param description: bool (search in description?)
        :param pr_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :return: re.Match or None
        """
        all_comments = self.get_pr_comments(pr_id=pr_id, reverse=reverse)
        if description:
            description_content = self.get_pr_info(pr_id).description
            if reverse:
                all_comments.append(description_content)
            else:
                all_comments.insert(0, description_content)

        pattern = re.compile(filter_regex)
        for comment in all_comments:
            if not isinstance(comment, six.string_types):
                comment = comment.comment
            re_search = pattern.search(comment)
            if re_search:
                return re_search
        return None

    def pr_create(self, title, body, target_branch, source_branch):
        """
        Create a new pull request.

        :param title: str
        :param body: str
        :param target_branch: str
        :param source_branch: str
        :return: PullRequest
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

    def get_git_urls(self):
        raise NotImplementedError()

    def fork_create(self):
        """
        Create a fork of the project.

        :return: GitProject
        """
        raise NotImplementedError()


class GitUser:
    def __init__(self, service):
        self.service = service

    def get_username(self):
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

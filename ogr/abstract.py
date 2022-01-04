# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import functools
from enum import Enum, IntEnum
from typing import (
    Optional,
    Match,
    List,
    Dict,
    Set,
    TypeVar,
    Any,
    Sequence,
    Union,
    Callable,
)

import github
import gitlab
import requests

from ogr.exceptions import (
    OgrException,
    GitlabAPIException,
    GithubAPIException,
    OgrNetworkError,
)
from ogr.parsing import parse_git_repo

try:
    from functools import cached_property as _cached_property
except ImportError:
    from functools import lru_cache

    def _cached_property(func):  # type: ignore
        return property(lru_cache()(func))


AnyComment = TypeVar("AnyComment", bound="Comment")


def catch_common_exceptions(function: Callable) -> Any:
    """
    Decorator catching common exceptions.

    Args:
        function (Callable): Function or method to decorate.

    Raises:
        GithubAPIException, if authentication to Github failed.
        GitlabAPIException, if authentication to Gitlab failed.
        OgrNetworkError, if network problems occurred while performing a request.
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except github.BadCredentialsException as ex:
            raise GithubAPIException("Invalid Github credentials") from ex
        except gitlab.GitlabAuthenticationError as ex:
            raise GitlabAPIException("Invalid Gitlab credentials") from ex
        except requests.exceptions.ConnectionError as ex:
            raise OgrNetworkError(
                "Could not perform the request due to a network error"
            ) from ex

    return wrapper


class CatchCommonErrors(type):
    """
    A metaclass wrapping methods with a common exception handler.

    This handler catches exceptions which can occur almost anywhere
    and catching them manually would be tedious and converts them
    to an appropriate ogr exception for the user. This includes
    exceptions such as:
        - authentication (from Github/Gitlab)
        - network errors
    """

    def __new__(cls, name, bases, namespace):
        for key, value in namespace.items():
            # There is an anticipated change in behaviour in Python 3.10
            # for static/class methods. From Python 3.10 they will be callable.
            # We need to achieve consistent behaviour with older versions,
            # hence the explicit handling is needed here (isinstance checking
            # works the same). Moreover, static/class method decorator must
            # be used last, especially prior to Python 3.10 since they return
            # descriptor objects and not functions.
            # See: https://bugs.python.org/issue43682
            if isinstance(value, staticmethod):
                namespace[key] = staticmethod(catch_common_exceptions(value.__func__))
            elif isinstance(value, classmethod):
                namespace[key] = classmethod(catch_common_exceptions(value.__func__))
            elif callable(namespace[key]):
                namespace[key] = catch_common_exceptions(namespace[key])
        return super().__new__(cls, name, bases, namespace)


class OgrAbstractClass(metaclass=CatchCommonErrors):
    def __repr__(self) -> str:
        return f"<{str(self)}>"


class Reaction(OgrAbstractClass):
    def __init__(self, raw_reaction: Any) -> None:
        self._raw_reaction = raw_reaction

    def __str__(self):
        return f"Reaction(raw_reaction={self._raw_reaction})"

    def delete(self) -> None:
        """Delete a reaction."""
        raise NotImplementedError()


class Comment(OgrAbstractClass):
    def __init__(
        self,
        raw_comment: Optional[Any] = None,
        parent: Optional[Any] = None,
        body: Optional[str] = None,
        id_: Optional[int] = None,
        author: Optional[str] = None,
        created: Optional[datetime.datetime] = None,
        edited: Optional[datetime.datetime] = None,
    ) -> None:
        if raw_comment:
            self._from_raw_comment(raw_comment)
        elif body and author:
            self._body = body
            self._id = id_
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
    def body(self) -> str:
        """Body of the comment."""
        return self._body

    @body.setter
    def body(self, new_body: str) -> None:
        self._body = new_body

    @property
    def id(self) -> int:
        return self._id

    @property
    def author(self) -> str:
        """Login of the author of the comment."""
        return self._author

    @property
    def created(self) -> datetime.datetime:
        """Datetime of creation of the comment."""
        return self._created

    @property
    def edited(self) -> datetime.datetime:
        """Datetime of last edit of the comment."""
        return self._edited

    def get_reactions(self) -> List[Reaction]:
        """Returns list of reactions."""
        raise NotImplementedError()

    def add_reaction(self, reaction: str) -> Reaction:
        """
        Reacts to a comment.

        Colons in between reaction are not needed, e.g. `comment.add_reaction("+1")`.

        Args:
            reaction: String representing specific reaction to be added.

        Returns:
            Object representing newly added reaction.
        """
        raise NotImplementedError()


class IssueComment(Comment):
    @property
    def issue(self) -> "Issue":
        """Issue of issue comment."""
        return self._parent

    def __str__(self) -> str:
        return "Issue" + super().__str__()


class PRComment(Comment):
    @property
    def pull_request(self) -> "PullRequest":
        """Pull request of pull request comment."""
        return self._parent

    def __str__(self) -> str:
        return "PR" + super().__str__()


class IssueStatus(IntEnum):
    """Enumeration for issue statuses."""

    open = 1
    closed = 2
    all = 3


class Issue(OgrAbstractClass):
    """
    Attributes:
        project (GitProject): Project of the issue.
    """

    def __init__(self, raw_issue: Any, project: "GitProject") -> None:
        self._raw_issue = raw_issue
        self.project = project

    @property
    def title(self) -> str:
        """Title of the issue."""
        raise NotImplementedError()

    @property
    def private(self) -> bool:
        """`True` if issue is confidential, `False` otherwise."""
        raise NotImplementedError()

    @property
    def id(self) -> int:
        """ID of the issue."""
        raise NotImplementedError()

    @property
    def status(self) -> IssueStatus:
        """Status of the issue."""
        raise NotImplementedError()

    @property
    def url(self) -> str:
        """Web URL of the issue."""
        raise NotImplementedError()

    @property
    def description(self) -> str:
        """Description of the issue."""
        raise NotImplementedError()

    @property
    def author(self) -> str:
        """Username of the author of the issue."""
        raise NotImplementedError()

    @property
    def created(self) -> datetime.datetime:
        """Datetime of the creation of the issue."""
        raise NotImplementedError()

    @property
    def labels(self) -> List:
        """Labels of the issue."""
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
    def create(
        project: Any,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> "Issue":
        """
        Open new issue.

        Args:
            project (GitProject): Project where the issue is to be opened.
            title: Title of the issue.
            body: Description of the issue.
            private: Is the new issue supposed to be confidential?

                **Supported only by GitLab and Pagure.**

                Defaults to unset.
            labels: List of labels that are to be added to
                the issue.

                Defaults to no labels.
            assignees: List of usernames of the assignees.

                Defaults to no assignees.

        Returns:
            Object that represents newly created issue.
        """
        raise NotImplementedError()

    @staticmethod
    def get(project: Any, id: int) -> "Issue":
        """
        Get issue.

        Args:
            project (GitProject): Project where the issue is to be opened.
            issue_id: ID of the issue.

        Returns:
            Object that represents requested issue.
        """
        raise NotImplementedError()

    @staticmethod
    def get_list(
        project: Any,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List["Issue"]:
        """
        List of issues.

        Args:
            project (GitProject): Project where the issue is to be opened.
            status: Status of the issues that are to be
                included in the list.

                Defaults to `IssueStatus.open`.
            author: Username of the author of the issues.

                Defaults to no filtering by author.
            assignee: Username of the assignee on the issues.

                Defaults to no filtering by assignees.
            labels: Filter issues that have set specific labels.

                Defaults to no filtering by labels.

        Returns:
            List of objects that represent requested issues.
        """
        raise NotImplementedError()

    def _get_all_comments(self) -> List[IssueComment]:
        """
        Get list of all issue comments.

        Returns:
            List of all comments on the issue.
        """
        raise NotImplementedError()

    def get_comments(
        self, filter_regex: str = None, reverse: bool = False, author: str = None
    ) -> List[IssueComment]:
        """
        Get list of issue comments.

        Args:
            filter_regex: Filter the comments' content with `re.search`.

                Defaults to `None`, which means no filtering.
            reverse: Whether the comments are to be returned in
                reversed order.

                Defaults to `False`.
            author: Filter the comments by author.

                Defaults to `None`, which means no filtering.

        Returns:
            List of issue comments.
        """
        raise NotImplementedError()

    def can_close(self, username: str) -> bool:
        """
        Check if user have permissions to modify an issue.

        Args:
            username: Login of the user.

        Returns:
            `True` if user can close the issue, `False` otherwise.
        """
        raise NotImplementedError()

    def comment(self, body: str) -> IssueComment:
        """
        Add new comment to the issue.

        Args:
            body: Text contents of the comment.

        Returns:
            Object that represents posted comment.
        """
        raise NotImplementedError()

    def close(self) -> "Issue":
        """
        Close an issue.

        Returns:
            Issue itself.
        """
        raise NotImplementedError()

    def add_label(self, *labels: str) -> None:
        """
        Add labels to the issue.

        Args:
            *labels: Labels to be added.
        """
        raise NotImplementedError()

    def add_assignee(self, *assignees: str) -> None:
        """
        Assign users to an issue.

        Args:
            *assignees: List of logins of the assignees.
        """
        raise NotImplementedError()

    def get_comment(self, comment_id: int) -> IssueComment:
        """
        Returns an issue comment.

        Args:
            comment_id: id of a comment

        Returns:
            Object representing an issue comment.
        """
        raise NotImplementedError()


class PRStatus(IntEnum):
    """Enumeration that represents statuses of pull requests."""

    open = 1
    closed = 2
    merged = 3
    all = 4


class CommitStatus(Enum):
    """Enumeration that represents possible state of commit statuses."""

    pending = 1
    success = 2
    failure = 3
    error = 4
    canceled = 5
    running = 6


class MergeCommitStatus(Enum):
    """Enumeration that represents possible states of merge states of PR/MR."""

    can_be_merged = 1
    cannot_be_merged = 2
    unchecked = 3
    checking = 4
    cannot_be_merged_recheck = 5


class PullRequest(OgrAbstractClass):
    """
    Attributes:
        project (GitProject): Project of the pull request.
    """

    def __init__(self, raw_pr: Any, project: "GitProject") -> None:
        self._raw_pr = raw_pr
        self._target_project = project

    @property
    def title(self) -> str:
        """Title of the pull request."""
        raise NotImplementedError()

    @title.setter
    def title(self, new_title: str) -> None:
        raise NotImplementedError()

    @property
    def id(self) -> int:
        """ID of the pull request."""
        raise NotImplementedError()

    @property
    def status(self) -> PRStatus:
        """Status of the pull request."""
        raise NotImplementedError()

    @property
    def url(self) -> str:
        """Web URL of the pull request."""
        raise NotImplementedError()

    @property
    def description(self) -> str:
        """Description of the pull request."""
        raise NotImplementedError()

    @description.setter
    def description(self, new_description: str) -> None:
        raise NotImplementedError

    @property
    def author(self) -> str:
        """Login of the author of the pull request."""
        raise NotImplementedError()

    @property
    def source_branch(self) -> str:
        """Name of the source branch (from which the changes are pulled)."""
        raise NotImplementedError()

    @property
    def target_branch(self) -> str:
        """Name of the target branch (where the changes are being merged)."""
        raise NotImplementedError()

    @property
    def created(self) -> datetime.datetime:
        """Datetime of creating the pull request."""
        raise NotImplementedError()

    @property
    def labels(self) -> List[Any]:
        """Labels of the pull request."""
        raise NotImplementedError()

    @property
    def diff_url(self) -> str:
        """Web URL to the diff of the pull request."""
        raise NotImplementedError()

    @property
    def patch(self) -> bytes:
        """Patch of the pull request."""
        raise NotImplementedError()

    @property
    def head_commit(self) -> str:
        """Commit hash of the HEAD commit of the pull request."""
        raise NotImplementedError()

    @property
    def target_branch_head_commit(self) -> str:
        """Commit hash of the HEAD commit of the target branch."""
        raise NotImplementedError()

    @property
    def merge_commit_sha(self) -> str:
        """
        Commit hash of the merge commit of the pull request.

        Before merging represents test merge commit, if git forge supports it.
        """
        raise NotImplementedError()

    @property
    def merge_commit_status(self) -> MergeCommitStatus:
        """Current status of the test merge commit."""
        raise NotImplementedError()

    @property
    def source_project(self) -> "GitProject":
        """Object that represents source project (from which the changes are pulled)."""
        raise NotImplementedError()

    @property
    def target_project(self) -> "GitProject":
        """Object that represents target project (where changes are merged)."""
        return self._target_project

    @property
    def commits_url(self) -> str:
        """Web URL to the list of commits in the pull request."""
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
            f"diff_url='{self.diff_url}', "
            f"description='{description}', "
            f"author='{self.author}', "
            f"source_branch='{self.source_branch}', "
            f"target_branch='{self.target_branch}', "
            f"created='{self.created}')"
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
        Create new pull request.

        Args:
            project (GitProject): Project where the pull request will be created.
            title: Title of the pull request.
            body: Description of the pull request.
            target_branch: Branch in the project where the changes are being
                merged.
            source_branch: Branch from which the changes are being pulled.
            fork_username: The username/namespace of the forked repository.

        Returns:
            Object that represents newly created pull request.
        """
        raise NotImplementedError()

    @staticmethod
    def get(project: Any, id: int) -> "PullRequest":
        """
        Get pull request.

        Args:
            project (GitProject): Project where the pull request is located.
            id: ID of the pull request.

        Returns:
            Object that represents pull request.
        """
        raise NotImplementedError()

    @staticmethod
    def get_list(project: Any, status: PRStatus = PRStatus.open) -> List["PullRequest"]:
        """
        List of pull requests.

        Args:
            project (GitProject): Project where the pull requests are located.
            status: Filters out the pull requests.

                Defaults to `PRStatus.open`.

        Returns:
            List of pull requests with requested status.
        """
        raise NotImplementedError()

    def update_info(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> "PullRequest":
        """
        Update pull request information.

        Args:
            title: The new title of the pull request.

                Defaults to `None`, which means no updating.
            description: The new description of the pull request.

                Defaults to `None`, which means no updating.

        Returns:
            Pull request itself.
        """
        raise NotImplementedError()

    def _get_all_comments(self) -> List[PRComment]:
        """
        Get list of all pull request comments.

        Returns:
            List of all comments on the pull request.
        """
        raise NotImplementedError()

    def get_comments(
        self,
        filter_regex: Optional[str] = None,
        reverse: bool = False,
        author: Optional[str] = None,
    ) -> List["PRComment"]:
        """
        Get list of pull request comments.

        Args:
            filter_regex: Filter the comments' content with `re.search`.

                Defaults to `None`, which means no filtering.
            reverse: Whether the comments are to be returned in
                reversed order.

                Defaults to `False`.
            author: Filter the comments by author.

                Defaults to `None`, which means no filtering.

        Returns:
            List of pull request comments.
        """
        raise NotImplementedError()

    def get_all_commits(self) -> List[str]:
        """
        Returns:
            List of commit hashes of commits in pull request.
        """
        raise NotImplementedError()

    def search(
        self, filter_regex: str, reverse: bool = False, description: bool = True
    ) -> Optional[Match[str]]:
        """
        Find match in pull request description or comments.

        Args:
            filter_regex: Regex that is used to filter the comments' content with `re.search`.
            reverse: Reverse order of the comments.

                Defaults to `False`.
            description: Whether description is included in the search.

                Defaults to `True`.

        Returns:
            `re.Match` if found, `None` otherwise.
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

        Args:
            body: Body of the comment.
            commit: Commit hash to which comment is related.

                Defaults to generic comment.
            filename: Path to the file to which comment is related.

                Defaults to no relation to the file.
            row: Line number to which the comment is related.

                Defaults to no relation to the line.

        Returns:
            Newly created comment.
        """
        raise NotImplementedError()

    def close(self) -> "PullRequest":
        """
        Close the pull request.

        Returns:
            Pull request itself.
        """
        raise NotImplementedError()

    def merge(self) -> "PullRequest":
        """
        Merge the pull request.

        Returns:
            Pull request itself.
        """
        raise NotImplementedError()

    def add_label(self, *labels: str) -> None:
        """
        Add labels to the pull request.

        Args:
            *labels: Labels to be added.
        """
        raise NotImplementedError()

    def get_statuses(self) -> List["CommitFlag"]:
        """
        Returns statuses for latest commit on pull request.

        Returns:
            List of commit statuses of the latest commit.
        """
        raise NotImplementedError()

    def get_comment(self, comment_id: int) -> PRComment:
        """
        Returns a PR comment.

        Args:
            comment_id: id of comment

        Returns:
            Object representing a PR comment.
        """
        raise NotImplementedError()


class CommitFlag(OgrAbstractClass):
    _states: Dict[str, CommitStatus] = {}

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
        self.uid = uid
        self.project = project
        self.commit = commit

        if commit and state and context:
            self.state = state
            self.context = context
            self.comment = comment
            self.url = url
        else:
            self._raw_commit_flag = raw_commit_flag
            self._from_raw_commit_flag()

    def __str__(self) -> str:
        return (
            f"CommitFlag("
            f"commit='{self.commit}', "
            f"state='{self.state.name}', "
            f"context='{self.context}', "
            f"uid='{self.uid}', "
            f"comment='{self.comment}', "
            f"url='{self.url}', "
            f"created='{self.created}', "
            f"edited='{self.edited}')"
        )

    @classmethod
    def _state_from_str(cls, state: str) -> CommitStatus:
        """
        Transforms state from string to enumeration.

        Args:
            state: String representation of a state.

        Returns:
            Commit status.
        """
        raise NotImplementedError()

    @classmethod
    def _validate_state(cls, state: CommitStatus) -> CommitStatus:
        """
        Validates state of the commit status (if it can be used with forge).
        """
        raise NotImplementedError()

    def _from_raw_commit_flag(self) -> None:
        """
        Sets attributes based on the raw flag that has been given through constructor.
        """
        raise NotImplementedError()

    @staticmethod
    def get(project: Any, commit: str) -> List["CommitFlag"]:
        """
        Acquire commit statuses for given commit in the project.

        Args:
            project (GitProject): Project where the commit is located.
            commit: Commit hash for which we request statuses.

        Returns:
            List of commit statuses for the commit.
        """
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
        """
        Set a new commit status.

        Args:
            project (GitProject): Project where the commit is located.
            commit: Commit hash for which we set status.
            state: State for the commit status.
            target_url: URL for the commit status.
            description: Description of the commit status.
            context: Identifier to group related commit statuses.
        """
        raise NotImplementedError()

    @property
    def created(self) -> datetime.datetime:
        """Datetime of creating the commit status."""
        raise NotImplementedError()

    @property
    def edited(self) -> datetime.datetime:
        """Datetime of editing the commit status."""
        raise NotImplementedError()


class CommitComment(OgrAbstractClass):
    """
    Attributes:
        sha (str): Hash of the related commit.
        comment (str): Body of the comment.
        author (str): Login of the author.
    """

    def __init__(self, sha: str, comment: str, author: str) -> None:
        self.sha = sha
        self.comment = comment
        self.author = author

    def __str__(self) -> str:
        return f"CommitComment(commit={self.sha}, author={self.author}, comment={self.comment})"


class GitTag(OgrAbstractClass):
    """
    Class representing a git tag.

    Attributes:
        name (str): Name of the tag.
        commit_sha (str): Commit hash of the tag.
    """

    def __init__(self, name: str, commit_sha: str) -> None:
        self.name = name
        self.commit_sha = commit_sha

    def __str__(self) -> str:
        return f"GitTag(name={self.name}, commit_sha={self.commit_sha})"


class AccessLevel(IntEnum):
    """
    Enumeration representing an access level to the repository.

    | Value from enumeration | GitHub   | GitLab                  | Pagure |
    | ---------------------- | -------- | ----------------------- | ------ |
    | `AccessLevel.pull`     | pull     | guest                   | ticket |
    | `AccessLevel.triage`   | triage   | reporter                | ticket |
    | `AccessLevel.push`     | push     | developer               | commit |
    | `AccessLevel.admin`    | admin    | maintainer              | commit |
    | `AccessLevel.maintain` | maintain | owner (only for groups) | admin  |
    """

    pull = 1
    triage = 2
    push = 3
    admin = 4
    maintain = 5


class Release(OgrAbstractClass):
    """
    Object that represents release.

    Attributes:
        project (GitProject): Project on which the release is created.
    """

    def __init__(
        self,
        raw_release: Any,
        project: "GitProject",
    ) -> None:
        self._raw_release = raw_release
        self.project = project

    def __str__(self) -> str:
        return (
            f"Release("
            f"title='{self.title}', "
            f"body='{self.body}', "
            f"tag_name='{self.tag_name}', "
            f"url='{self.url}', "
            f"created_at='{self.created_at}', "
            f"tarball_url='{self.tarball_url}')"
        )

    @property
    def title(self) -> str:
        """Title of the release."""
        raise NotImplementedError()

    @property
    def body(self) -> str:
        """Body of the release."""
        raise NotImplementedError()

    @property
    def git_tag(self) -> GitTag:
        """Object that represents tag tied to the release."""
        raise NotImplementedError()

    @property
    def tag_name(self) -> str:
        """Tag tied to the release."""
        raise NotImplementedError()

    @property
    def url(self) -> Optional[str]:
        """URL of the release."""
        raise NotImplementedError()

    # TODO: Check if should really be string
    @property
    def created_at(self) -> datetime.datetime:
        """Datetime of creating the release."""
        raise NotImplementedError()

    @property
    def tarball_url(self) -> str:
        """URL of the tarball."""
        raise NotImplementedError()

    @staticmethod
    def get(
        project: Any,
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> "Release":
        """
        Get a single release.

        Args:
            identifier: Identifier of the release.

                Defaults to `None`, which means not being used.
            name: Name of the release.

                Defaults to `None`, which means not being used.
            tag_name: Tag that the release is tied to.

                Defaults to `None`, which means not being used.

        Returns:
            Object that represents release that satisfies requested condition.
        """
        raise NotImplementedError()

    @staticmethod
    def get_latest(project: Any) -> Optional["Release"]:
        """
        Returns:
            Object that represents the latest release.
        """
        raise NotImplementedError()

    @staticmethod
    def get_list(project: Any) -> List["Release"]:
        """
        Returns:
            List of the objects that represent releases.
        """
        raise NotImplementedError()

    @staticmethod
    def create(
        project: Any,
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "Release":
        """
        Create new release.

        Args:
            project: Project where the release is to be created.
            tag: Tag which is the release based off.
            name: Name of the release.
            message: Message or description of the release.
            ref: Git reference, mainly commit hash for the release. If provided
                git tag is created prior to creating a release.

                Defaults to `None`.

        Returns:
            Object that represents newly created release.
        """
        raise NotImplementedError()

    def save_archive(self, filename: str) -> None:
        """
        Save tarball of the release to requested `filename`.

        Args:
            filename: Path to the file to save archive to.
        """
        raise NotImplementedError()

    def edit_release(self, name: str, message: str) -> None:
        """
        Edit name and message of a release.

        Args:
            name: Name of the release.
            message: Description of the release.
        """
        raise NotImplementedError()


class GitService(OgrAbstractClass):
    """
    Attributes:
        instance_url (str): URL of the git forge instance.
    """

    instance_url: Optional[str] = None

    def __init__(self, **_: Any) -> None:
        pass

    def __str__(self) -> str:
        return f"GitService(instance_url={self.instance_url})"

    def get_project(self, **kwargs: Any) -> "GitProject":
        """
        Get the requested project.

        Args:
            namespace (str): Namespace of the project.
            user (str): Username of the project's owner.
            repo (str): Repository name.

        Returns:
            Object that represents git project.
        """
        raise NotImplementedError

    def get_project_from_url(self, url: str) -> "GitProject":
        """
        Args:
            url: URL of the git repository.

        Returns:
            Object that represents project from the parsed URL.
        """
        repo_url = parse_git_repo(potential_url=url)
        if not repo_url:
            raise OgrException(f"Failed to find repository for url: {url}")
        return self.get_project(repo=repo_url.repo, namespace=repo_url.namespace)

    @_cached_property
    def hostname(self) -> Optional[str]:
        """Hostname of the service."""
        raise NotImplementedError

    @property
    def user(self) -> "GitUser":
        """User authenticated through the service."""
        raise NotImplementedError

    def change_token(self, new_token: str) -> None:
        """
        Change an API token. Only for the current instance and newly created projects.

        Args:
            new_token: New token to be set.
        """
        raise NotImplementedError

    def project_create(
        self,
        repo: str,
        namespace: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "GitProject":
        """
        Create new project.

        Args:
            repo: Name of the newly created project.
            namespace: Namespace of the newly created project.

                Defaults to currently authenticated user.
            description: Description of the newly created project.

        Returns:
            Object that represents newly created project.
        """
        raise NotImplementedError()

    def list_projects(
        self,
        namespace: str = None,
        user: str = None,
        search_pattern: str = None,
        language: str = None,
    ) -> List["GitProject"]:
        """
        List projects for given criteria.

        Args:
            namespace: Namespace to list projects from.
            user: Login of the owner of the projects.
            search_pattern: Regular expression that repository name should match.
            language: Language to be present in the project, e.g. `"python"` or
                `"html"`.
        """
        raise NotImplementedError


class GitProject(OgrAbstractClass):
    def __init__(self, repo: str, service: GitService, namespace: str) -> None:
        """
        Args:
            repo: Name of the project.
            service: GitService instance.
            namespace: Namespace of the project.

                - GitHub: username or org name.
                - GitLab: username or org name.
                - Pagure: namespace (e.g. `"rpms"`).

                  In case of forks: `"fork/{username}/{namespace}"`.
        """
        self.service = service
        self.repo = repo
        self.namespace = namespace

    def __str__(self) -> str:
        return f"GitProject(namespace={self.namespace}, repo={self.repo}, service={self.service})"

    @property
    def description(self) -> str:
        """
        Returns:
            Project description.
        """
        raise NotImplementedError()

    @description.setter
    def description(self, new_description: str) -> None:
        """
        Args:
            new_description: description to set for project.
        """
        raise NotImplementedError()

    def delete(self) -> None:
        """Delete the project."""
        raise NotImplementedError()

    def exists(self) -> bool:
        """
        Check the existence of the repo.

        Returns:
            `True` if the project exists, `False` otherwise.
        """
        raise NotImplementedError()

    def is_private(self) -> bool:
        """
        Is this repository private (accessible only by users with permissions).

        Returns:
            `True`, if the repository is private.
        """
        raise NotImplementedError()

    def is_forked(self) -> bool:
        """
        Is this repository forked by the authenticated user?

        Returns:
            `True`, if the repository is fork.
        """
        raise NotImplementedError()

    @property
    def is_fork(self) -> bool:
        """`True` if the project is a fork."""
        raise NotImplementedError()

    @property
    def full_repo_name(self) -> str:
        """Get repo name with namespace, e.g. `rpms/python-docker-py`."""
        raise NotImplementedError()

    @property
    def parent(self) -> Optional["GitProject"]:
        """Parent project if the project is a fork, otherwise `None`."""
        raise NotImplementedError()

    def get_branches(self) -> List[str]:
        """
        Returns:
            List with names of branches in the project.
        """
        raise NotImplementedError()

    @property
    def default_branch(self) -> str:
        """Default branch (usually `main`, `master` or `trunk`)."""
        raise NotImplementedError()

    def get_description(self) -> str:
        """
        Returns:
            Project description.
        """
        raise NotImplementedError()

    def get_fork(self, create: bool = True) -> Optional["GitProject"]:
        """
        Provide GitProject instance of a fork of this project.

        Args:
            create: Create fork if it does not exist.

        Returns:
            `None` if the project is fork itself or there is no fork, otherwise
            instance of a fork if is to be created or exists already.
        """
        raise NotImplementedError()

    def get_owners(self) -> List[str]:
        """
        Returns:
            List of usernames of project owners.
        """
        raise NotImplementedError()

    def who_can_close_issue(self) -> Set[str]:
        """
        Returns:
            Names of all users who have permission to modify an issue.
        """
        raise NotImplementedError()

    def who_can_merge_pr(self) -> Set[str]:
        """
        Returns:
            Names of all users who have permission to modify pull request.
        """
        raise NotImplementedError()

    def can_merge_pr(self, username: str) -> bool:
        """
        Args:
            username: Username.

        Returns:
            `True` if user merge pull request, `False` otherwise.
        """
        raise NotImplementedError()

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        """
        Add user to project.

        Args:
            user: Username of the user.
            access_level: Permissions for the user.
        """
        raise NotImplementedError()

    def request_access(self) -> None:
        """
        Request an access to the project (cannot specify access level to be granted;
        needs to be approved and specified by the user with maintainer/admin rights).
        """
        raise NotImplementedError()

    def add_group(self, group: str, access_level: AccessLevel) -> None:
        """
        Add group to project.

        Args:
            group: Name of the group.
            access_level: Permissions for the group.
        """
        raise NotImplementedError

    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List["Issue"]:
        """
        List of issues.

        Args:
            status: Status of the issues that are to be
                included in the list.

                Defaults to `IssueStatus.open`.
            author: Username of the author of the issues.

                Defaults to no filtering by author.
            assignee: Username of the assignee on the issues.

                Defaults to no filtering by assignees.
            labels: Filter issues that have set specific labels.

                Defaults to no filtering by labels.

        Returns:
            List of objects that represent requested issues.
        """
        raise NotImplementedError()

    def get_issue(self, issue_id: int) -> "Issue":
        """
        Get issue.

        Args:
            issue_id: ID of the issue.

        Returns:
            Object that represents requested issue.
        """
        raise NotImplementedError()

    def get_issue_info(self, issue_id: int) -> "Issue":
        """
        Get issue info.

        Args:
            issue_id: ID of the issue.

        Returns:
            Object that represents requested issue.
        """
        raise NotImplementedError()

    def create_issue(
        self,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Issue:
        """
        Open new issue.

        Args:
            title: Title of the issue.
            body: Description of the issue.
            private: Is the new issue supposed to be confidential?

                **Supported only by GitLab and Pagure.**

                Defaults to unset.
            labels: List of labels that are to be added to
                the issue.

                Defaults to no labels.
            assignees: List of usernames of the assignees.

                Defaults to no assignees.

        Returns:
            Object that represents newly created issue.
        """
        raise NotImplementedError()

    def get_pr_list(self, status: PRStatus = PRStatus.open) -> List["PullRequest"]:
        """
        List of pull requests.

        Args:
            status: Status of the pull requests that are to be included in the list.

                Defaults to `PRStatus.open`.

        Returns:
            List of objects that represent pull requests with requested status.
        """
        raise NotImplementedError()

    def get_pr(self, pr_id: int) -> "PullRequest":
        """
        Get pull request.

        Args:
            pr_id: ID of the pull request.

        Returns:
            Object that represents requested pull request.
        """
        raise NotImplementedError()

    def get_tags(self) -> List["GitTag"]:
        """
        Returns:
            List of objects that represent tags.
        """
        raise NotImplementedError()

    def get_sha_from_tag(self, tag_name: str) -> str:
        """
        Args:
            tag_name: Name of the tag.

        Returns:
            Commit hash of the commit from the requested tag.
        """
        raise NotImplementedError()

    def get_release(
        self,
        identifier: Optional[int] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
    ) -> Release:
        """
        Get a single release.

        Args:
            identifier: Identifier of the release.

                Defaults to `None`, which means not being used.
            name: Name of the release.

                Defaults to `None`, which means not being used.
            tag_name: Tag that the release is tied to.

                Defaults to `None`, which means not being used.

        Returns:
            Object that represents release that satisfies requested condition.
        """
        raise NotImplementedError()

    def get_latest_release(self) -> Optional[Release]:
        """
        Returns:
            Object that represents the latest release.
        """
        raise NotImplementedError()

    def get_releases(self) -> List[Release]:
        """
        Returns:
            List of the objects that represent releases.
        """
        raise NotImplementedError()

    def create_release(
        self, tag: str, name: str, message: str, ref: Optional[str] = None
    ) -> Release:
        """
        Create new release.

        Args:
            tag: Tag which is the release based off.
            name: Name of the release.
            message: Message or description of the release.
            ref: Git reference, mainly commit hash for the release. If provided
                git tag is created prior to creating a release.

                Defaults to `None`.

        Returns:
            Object that represents newly created release.
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
        Create new pull request.

        Args:
            title: Title of the pull request.
            body: Description of the pull request.
            target_branch: Name of the branch where the changes are merged.
            source_branch: Name of the branch from which the changes are pulled.
            fork_username: The username of forked repository.

                Defaults to `None`.

        Returns:
            Object that represents newly created pull request.
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

        Args:
            commit: Hash of the commit.
            body: Body of the comment.
            filename: Name of the file that is related to the comment.

                Defaults to `None`, which means no relation to file.
            row: Number of the row that the comment is related to.

                Defaults to `None`, which means no relation to the row.

        Returns:
            Object that represents newly created commit comment.
        """
        raise NotImplementedError()

    def set_commit_status(
        self,
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "CommitFlag":
        """
        Create a status on a commit.

        Args:
            commit: The hash of the commit.
            state: The state of the status.
            target_url: The target URL to associate with this status.
            description: A short description of the status.
            context: A label to differentiate this status from the status of other systems.
            trim: Whether to trim the description to 140 characters.

                Defaults to `False`.

        Returns:
            Object that represents created commit status.
        """
        raise NotImplementedError()

    def get_commit_statuses(self, commit: str) -> List[CommitFlag]:
        """
        Get statuses of the commit.

        Args:
            commit: Hash of the commit.

        Returns:
            List of all commit statuses on the commit.
        """
        raise NotImplementedError()

    def get_git_urls(self) -> Dict[str, str]:
        """
        Get git URLs for the project.

        Returns:
            Dictionary with at least SSH and HTTP URLs for the current project.
        """
        raise NotImplementedError()

    def fork_create(self) -> "GitProject":
        """
        Fork this project using the authenticated user.

        Returns:
            Fork of the current project.

        Raises:
            In case the fork already exists.
        """
        raise NotImplementedError()

    def change_token(self, new_token: str) -> None:
        """
        Change an API token. Only for the current instance.

        Args:
            new_token: New token to be set.
        """
        raise NotImplementedError

    def get_file_content(self, path: str, ref: str = None) -> str:
        """
        Get a content of the file in the repo.

        Args:
            path: Path to the file.
            ref: Branch or commit.

                Defaults to repo's default branch.

        Returns:
            Contents of the file as string.

        Raises:
            FileNotFoundError: if there is no such file.
        """
        raise NotImplementedError

    def get_files(
        self, ref: str = None, filter_regex: str = None, recursive: bool = False
    ) -> List[str]:
        """
        Get a list of file paths of the repo.

        Args:
            ref: Branch or commit.

                Defaults to repo's default branch.
            filter_regex: Filter the paths with `re.search`.

                Defaults to `None`, which means no filtering.
            recursive: Whether to return only top directory files
                or all files recursively.

                Defaults to `False`, which means only top-level directory.

        Returns:
            List of paths of the files in the repo.
        """
        raise NotImplementedError

    def get_forks(self) -> Sequence["GitProject"]:
        """
        Returns:
            All forks of the project.
        """
        raise NotImplementedError()

    def get_web_url(self) -> str:
        """
        Returns:
            Web URL of the project.
        """
        raise NotImplementedError()

    def get_sha_from_branch(self, branch: str) -> Optional[str]:
        """
        Returns:
            Commit SHA of head of the branch. `None` if no branch was found.
        """
        raise NotImplementedError()


class GitUser(OgrAbstractClass):
    """
    Represents currently authenticated user through service.
    """

    def __init__(self, service: GitService) -> None:
        self.service = service

    def get_username(self) -> str:
        """
        Returns:
            Login of the user.
        """
        raise NotImplementedError()

    def get_email(self) -> str:
        """
        Returns:
            Email of the user.
        """
        raise NotImplementedError()

    def get_projects(self) -> Sequence["GitProject"]:
        """
        Returns:
            Sequence of projects in user's namespace.
        """
        raise NotImplementedError()

    def get_forks(self) -> Sequence["GitProject"]:
        """
        Returns:
            Sequence of forks in user's namespace.
        """
        raise NotImplementedError()

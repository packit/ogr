# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from collections.abc import Iterable, Sequence
from typing import Optional, Union

from ogr import abstract as _abstract
from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.access_level import AccessLevel
from ogr.abstract.git_tag import GitTag
from ogr.abstract.status import CommitStatus, IssueStatus, PRStatus


class GitProject(OgrAbstractClass):
    def __init__(
        self,
        repo: str,
        service: "_abstract.GitService",
        namespace: str,
    ) -> None:
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

    @property
    def has_issues(self) -> bool:
        """`True` if issues are enabled on the project."""
        raise NotImplementedError()

    def get_branches(self) -> Union[list[str], Iterable[str]]:
        """
        Returns:
            List with names of branches in the project.
        """
        raise NotImplementedError()

    @property
    def default_branch(self) -> str:
        """Default branch (usually `main`, `master` or `trunk`)."""
        raise NotImplementedError()

    def get_commits(self, ref: Optional[str] = None) -> Union[list[str], Iterable[str]]:
        """
        Get list of commits for the project.

        Args:
            ref: Ref to start listing commits from, defaults to the default project branch.

        Returns:
            List of commit SHAs for the project.
        """
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

    def get_owners(self) -> Union[list[str], Iterable[str]]:
        """
        Returns:
            List of usernames of project owners.
        """
        raise NotImplementedError()

    def who_can_close_issue(self) -> set[str]:
        """
        Returns:
            Names of all users who have permission to modify an issue.
        """
        raise NotImplementedError()

    def who_can_merge_pr(self) -> set[str]:
        """
        Returns:
            Names of all users who have permission to modify pull request.
        """
        raise NotImplementedError()

    def which_groups_can_merge_pr(self) -> set[str]:
        """
        Returns:
            Names of all groups that have permission to modify pull request.
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

    def get_users_with_given_access(self, access_levels: list[AccessLevel]) -> set[str]:
        """
        Args:
            access_levels: list of access levels

        Returns:
            set of users with given access levels
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

    def remove_user(self, user: str) -> None:
        """
        Remove user from project.

        Args:
            user: Username of the user.
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
        raise NotImplementedError()

    def remove_group(self, group: str) -> None:
        """
        Remove group from project.

        Args:
            group: Name of the group.
        """
        raise NotImplementedError()

    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> Union[list["_abstract.Issue"], Iterable["_abstract.Issue"]]:
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

    def get_issue(self, issue_id: int) -> "_abstract.Issue":
        """
        Get issue.

        Args:
            issue_id: ID of the issue.

        Returns:
            Object that represents requested issue.
        """
        raise NotImplementedError()

    def get_issue_info(self, issue_id: int) -> "_abstract.Issue":
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
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> "_abstract.Issue":
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

        Raises:
            IssueTrackerDisabled, if issue tracker is disabled.
        """
        raise NotImplementedError()

    def get_pr_list(
        self,
        status: PRStatus = PRStatus.open,
    ) -> Union[list["_abstract.PullRequest"], Iterable["_abstract.PullRequest"]]:
        """
        List of pull requests.

        Args:
            status: Status of the pull requests that are to be included in the list.

                Defaults to `PRStatus.open`.

        Returns:
            List of objects that represent pull requests with requested status.
        """
        raise NotImplementedError()

    def get_pr(self, pr_id: int) -> "_abstract.PullRequest":
        """
        Get pull request.

        Args:
            pr_id: ID of the pull request.

        Returns:
            Object that represents requested pull request.
        """
        raise NotImplementedError()

    def get_pr_files_diff(
        self,
        pr_id: int,
        retries: int = 0,
        wait_seconds: int = 3,
    ) -> dict:
        """
        Get files diff of a pull request.

        Args:
            pr_id: ID of the pull request.

        Returns:
            Dictionary representing files diff.
        """
        raise NotImplementedError()

    def get_tags(self) -> Union[list["GitTag"], Iterable["GitTag"]]:
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
    ) -> "_abstract.Release":
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

    def get_latest_release(self) -> Optional["_abstract.Release"]:
        """
        Returns:
            Object that represents the latest release.
        """
        raise NotImplementedError()

    def get_releases(
        self,
    ) -> Union[list["_abstract.Release"], Iterable["_abstract.Release"]]:
        """
        Returns:
            List of the objects that represent releases.
        """
        raise NotImplementedError()

    def create_release(
        self,
        tag: str,
        name: str,
        message: str,
        ref: Optional[str] = None,
    ) -> "_abstract.Release":
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
        fork_username: Optional[str] = None,
    ) -> "_abstract.PullRequest":
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
    ) -> "_abstract.CommitComment":
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

    def get_commit_comments(
        self,
        commit: str,
    ) -> Union[list["_abstract.CommitComment"], Iterable["_abstract.CommitComment"]]:
        """
        Get comments for a commit.

        Args:
            commit: The hash of the commit.

        Returns:
            List of all comments for the commit.
        """
        raise NotImplementedError()

    def get_commit_comment(
        self,
        commit_sha: str,
        comment_id: int,
    ) -> "_abstract.CommitComment":
        """
        Get commit comment.

        Args:
            commit_sha: SHA of the commit
            comment_id: ID of the commit comment

        Returns:
            Object representing the commit comment.
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
    ) -> "_abstract.CommitFlag":
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

    def get_commit_statuses(
        self,
        commit: str,
    ) -> Union[list["_abstract.CommitFlag"], Iterable["_abstract.CommitFlag"]]:
        """
        Get statuses of the commit.

        Args:
            commit: Hash of the commit.

        Returns:
            List of all commit statuses on the commit.
        """
        raise NotImplementedError()

    def get_git_urls(self) -> dict[str, str]:
        """
        Get git URLs for the project.

        Returns:
            Dictionary with at least SSH and HTTP URLs for the current project.
        """
        raise NotImplementedError()

    def fork_create(self, namespace: Optional[str] = None) -> "GitProject":
        """
        Fork this project using the authenticated user.

        Args:
            namespace: Namespace where the project should be forked.

                Defaults to `None`, which means forking to the namespace of
                currently authenticated user.

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

    def get_file_content(
        self,
        path: str,
        ref: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> str:
        """
        Get a content of the file in the repo.

        Args:
            path: Path to the file.
            ref: Branch or commit.

                Defaults to repo's default branch.
            headers: Additional headers to be sent with the request.

                Defaults to `None`, which means no headers.

        Returns:
            Contents of the file as string.

        Raises:
            FileNotFoundError: if there is no such file.
        """
        raise NotImplementedError

    def get_files(
        self,
        ref: Optional[str] = None,
        filter_regex: Optional[str] = None,
        recursive: bool = False,
    ) -> Union[list[str], Iterable[str]]:
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

    def get_forks(self) -> Union[Sequence["GitProject"], Iterable["GitProject"]]:
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

    def get_contributors(self) -> set[str]:
        """
        Returns:
            Set of all contributors to the given project.
        """
        raise NotImplementedError()

    def users_with_write_access(self) -> set[str]:
        """
        Returns:
            List of users who have write access to the project
        """
        raise NotImplementedError("Use subclass instead.")

    def has_write_access(self, user: str) -> bool:
        """
        Decides whether a given user has write access to the project.

        Args:
            user: The user we are going to check to see if he/she has access
        """
        return user in self.users_with_write_access()

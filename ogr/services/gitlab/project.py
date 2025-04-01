# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging
import os
from typing import Any, Optional, Union

import gitlab
from gitlab.exceptions import GitlabGetError
from gitlab.v4.objects import Project as GitlabObjectsProject
from gitlab.v4.objects import ProjectCommit

from ogr.abstract import (
    AccessLevel,
    CommitComment,
    CommitFlag,
    CommitStatus,
    GitTag,
    Issue,
    IssueStatus,
    PRStatus,
    PullRequest,
    Release,
)
from ogr.exceptions import GitlabAPIException, OperationNotSupported
from ogr.services import gitlab as ogr_gitlab
from ogr.services.base import BaseGitProject
from ogr.services.gitlab.comments import GitlabCommitComment
from ogr.services.gitlab.flag import GitlabCommitFlag
from ogr.services.gitlab.issue import GitlabIssue
from ogr.services.gitlab.pull_request import GitlabPullRequest
from ogr.services.gitlab.release import GitlabRelease
from ogr.utils import filter_paths, indirect

logger = logging.getLogger(__name__)


class GitlabProject(BaseGitProject):
    service: "ogr_gitlab.GitlabService"

    def __init__(
        self,
        repo: str,
        service: "ogr_gitlab.GitlabService",
        namespace: str,
        gitlab_repo=None,
        **unprocess_kwargs,
    ) -> None:
        if unprocess_kwargs:
            logger.warning(
                f"GitlabProject will not process these kwargs: {unprocess_kwargs}",
            )
        super().__init__(repo, service, namespace)
        self._gitlab_repo = gitlab_repo
        self.read_only = False

    @property
    def gitlab_repo(self) -> GitlabObjectsProject:
        if not self._gitlab_repo:
            self._gitlab_repo = self.service.gitlab_instance.projects.get(
                f"{self.namespace}/{self.repo}",
            )
        return self._gitlab_repo

    @property
    def is_fork(self) -> bool:
        return bool("forked_from_project" in self.gitlab_repo.attributes)

    @property
    def parent(self) -> Optional["GitlabProject"]:
        if self.is_fork:
            parent_dict = self.gitlab_repo.attributes["forked_from_project"]
            return GitlabProject(
                repo=parent_dict["path"],
                service=self.service,
                namespace=parent_dict["namespace"]["full_path"],
            )
        return None

    @property
    def default_branch(self) -> Optional[str]:
        return self.gitlab_repo.attributes.get("default_branch")

    def __str__(self) -> str:
        return f'GitlabProject(namespace="{self.namespace}", repo="{self.repo}")'

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, GitlabProject):
            return False

        return (
            self.repo == o.repo
            and self.namespace == o.namespace
            and self.service == o.service
        )

    @property
    def has_issues(self) -> bool:
        return self.gitlab_repo.issues_enabled

    def _construct_fork_project(self) -> Optional["GitlabProject"]:
        user_login = self.service.user.get_username()
        try:
            project = GitlabProject(
                repo=self.repo,
                service=self.service,
                namespace=user_login,
            )
            if project.gitlab_repo:
                return project
        except Exception as ex:
            logger.debug(f"Project {user_login}/{self.repo} does not exist: {ex}")
        return None

    def exists(self) -> bool:
        try:
            _ = self.gitlab_repo
            return True
        except gitlab.exceptions.GitlabGetError as ex:
            if "404 Project Not Found" in str(ex):
                return False
            raise GitlabAPIException from ex

    def is_private(self) -> bool:
        return self.gitlab_repo.attributes["visibility"] == "private"

    def is_forked(self) -> bool:
        return bool(self._construct_fork_project())

    def get_description(self) -> str:
        return self.gitlab_repo.attributes["description"]

    @property
    def description(self) -> str:
        return self.gitlab_repo.attributes["description"]

    @description.setter
    def description(self, new_description: str) -> None:
        self.gitlab_repo.description = new_description
        self.gitlab_repo.save()

    def get_fork(self, create: bool = True) -> Optional["GitlabProject"]:
        username = self.service.user.get_username()
        for fork in self.get_forks():
            if fork.gitlab_repo.namespace["full_path"] == username:
                return fork

        if not self.is_forked():
            if create:
                return self.fork_create()

            logger.info(
                f"Fork of {self.gitlab_repo.attributes['name']}"
                " does not exist and we were asked not to create it.",
            )
            return None
        return self._construct_fork_project()

    def get_owners(self) -> list[str]:
        return self._get_collaborators_with_given_access(
            access_levels=[gitlab.const.OWNER_ACCESS],
        )

    def who_can_close_issue(self) -> set[str]:
        return set(
            self._get_collaborators_with_given_access(
                access_levels=[
                    gitlab.const.REPORTER_ACCESS,
                    gitlab.const.DEVELOPER_ACCESS,
                    gitlab.const.MAINTAINER_ACCESS,
                    gitlab.const.OWNER_ACCESS,
                ],
            ),
        )

    def who_can_merge_pr(self) -> set[str]:
        return set(
            self._get_collaborators_with_given_access(
                access_levels=[
                    gitlab.const.DEVELOPER_ACCESS,
                    gitlab.const.MAINTAINER_ACCESS,
                    gitlab.const.OWNER_ACCESS,
                ],
            ),
        )

    def can_close_issue(self, username):
        return username in self.who_can_close_issue()

    def can_merge_pr(self, username) -> bool:
        return username in self.who_can_merge_pr()

    def delete(self) -> None:
        self.gitlab_repo.delete()

    def _get_collaborators_with_given_access(
        self,
        access_levels: list[int],
    ) -> list[str]:
        """
        Get all project collaborators with one of the given access levels.
        Access levels:
            10 => Guest access
            20 => Reporter access
            30 => Developer access
            40 => Maintainer access
            50 => Owner access

        Returns:
            List of usernames.
        """
        # TODO: Remove once ‹members_all› is available for all releases of ogr
        all_members = None
        if hasattr(self.gitlab_repo, "members_all"):
            all_members = self.gitlab_repo.members_all.list(all=True)
        else:
            all_members = self.gitlab_repo.members.all(all=True)

        response = []
        for member in all_members:
            if isinstance(member, dict):
                access_level = member["access_level"]
                username = member["username"]
            else:
                access_level = member.access_level
                username = member.username
            if access_level in access_levels:
                response.append(username)
        return response

    def add_user(self, user: str, access_level: AccessLevel) -> None:
        access_dict = {
            AccessLevel.pull: gitlab.const.GUEST_ACCESS,
            AccessLevel.triage: gitlab.const.REPORTER_ACCESS,
            AccessLevel.push: gitlab.const.DEVELOPER_ACCESS,
            AccessLevel.admin: gitlab.const.MAINTAINER_ACCESS,
            AccessLevel.maintain: gitlab.const.OWNER_ACCESS,
        }
        try:
            user_id = self.service.gitlab_instance.users.list(username=user)[0].id
        except Exception as e:
            raise GitlabAPIException(f"User {user} not found") from e
        try:
            self.gitlab_repo.members.create(
                {"user_id": user_id, "access_level": access_dict[access_level]},
            )
        except Exception as e:
            raise GitlabAPIException(f"User {user} already exists") from e

    def request_access(self) -> None:
        try:
            self.gitlab_repo.accessrequests.create({})
        except gitlab.exceptions.GitlabCreateError as e:
            raise GitlabAPIException("Unable to request access") from e

    @indirect(GitlabPullRequest.get_list)
    def get_pr_list(self, status: PRStatus = PRStatus.open) -> list["PullRequest"]:
        pass

    def get_sha_from_tag(self, tag_name: str) -> str:
        try:
            tag = self.gitlab_repo.tags.get(tag_name)
            return tag.attributes["commit"]["id"]
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Tag {tag_name} was not found.")
            raise GitlabAPIException(f"Tag {tag_name} was not found.") from ex

    @indirect(GitlabPullRequest.create)
    def create_pr(
        self,
        title: str,
        body: str,
        target_branch: str,
        source_branch: str,
        fork_username: Optional[str] = None,
    ) -> "PullRequest":
        pass

    def commit_comment(
        self,
        commit: str,
        body: str,
        filename: Optional[str] = None,
        row: Optional[int] = None,
    ) -> "CommitComment":
        try:
            commit_object: ProjectCommit = self.gitlab_repo.commits.get(commit)
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Commit {commit} was not found.")
            raise GitlabAPIException(f"Commit {commit} was not found.") from ex

        if filename and row:
            raw_comment = commit_object.comments.create(
                {"note": body, "path": filename, "line": row, "line_type": "new"},
            )
        else:
            raw_comment = commit_object.comments.create({"note": body})
        return self._commit_comment_from_gitlab_object(raw_comment, commit)

    @staticmethod
    def _commit_comment_from_gitlab_object(raw_comment, commit: str) -> CommitComment:
        return GitlabCommitComment(
            raw_comment=raw_comment,
            sha=commit,
        )

    def get_commit_comments(self, commit: str) -> list[CommitComment]:
        try:
            commit_object: ProjectCommit = self.gitlab_repo.commits.get(commit)
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Commit {commit} was not found.")
            raise GitlabAPIException(f"Commit {commit} was not found.") from ex

        return [
            self._commit_comment_from_gitlab_object(comment, commit)
            for comment in commit_object.comments.list(all=True)
        ]

    def get_commit_comment(self, commit_sha: str, comment_id: int) -> CommitComment:
        try:
            commit_object: ProjectCommit = self.gitlab_repo.commits.get(commit_sha)
        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Commit with SHA {commit_sha} was not found: {ex}")
            raise GitlabAPIException(
                f"Commit with SHA {commit_sha} was not found.",
            ) from ex

        try:
            discussions = commit_object.discussions.list(all=True)
            comment = None

            for discussion in discussions:
                note_ids = [note["id"] for note in discussion.attributes["notes"]]
                if comment_id in note_ids:
                    comment = discussion.notes.get(comment_id)
                    break

            if comment is None:
                raise GitlabAPIException(
                    f"Comment with ID {comment_id} not found in commit {commit_sha}.",
                )

        except gitlab.exceptions.GitlabGetError as ex:
            logger.error(f"Failed to retrieve comment with ID {comment_id}: {ex}")
            raise GitlabAPIException(
                f"Failed to retrieve comment with ID {comment_id}.",
            ) from ex

        return self._commit_comment_from_gitlab_object(comment, commit_sha)

    @indirect(GitlabCommitFlag.set)
    def set_commit_status(
        self,
        commit: str,
        state: Union[CommitStatus, str],
        target_url: str,
        description: str,
        context: str,
        trim: bool = False,
    ) -> "CommitFlag":
        pass

    @indirect(GitlabCommitFlag.get)
    def get_commit_statuses(self, commit: str) -> list[CommitFlag]:
        pass

    def get_git_urls(self) -> dict[str, str]:
        return {
            "git": self.gitlab_repo.attributes["http_url_to_repo"],
            "ssh": self.gitlab_repo.attributes["ssh_url_to_repo"],
        }

    def fork_create(self, namespace: Optional[str] = None) -> "GitlabProject":
        data = {}
        if namespace:
            data["namespace_path"] = namespace

        try:
            fork = self.gitlab_repo.forks.create(data=data)
        except gitlab.GitlabCreateError as ex:
            logger.error(f"Repo {self.gitlab_repo} cannot be forked")
            raise GitlabAPIException(
                f"Repo {self.gitlab_repo} cannot be forked",
            ) from ex
        logger.debug(f"Forked to {fork.namespace['full_path']}/{fork.path}")
        return GitlabProject(
            namespace=fork.namespace["full_path"],
            service=self.service,
            repo=fork.path,
        )

    def change_token(self, new_token: str):
        self.service.change_token(new_token)

    def get_branches(self) -> list[str]:
        return [branch.name for branch in self.gitlab_repo.branches.list(all=True)]

    def get_commits(self, ref: Optional[str] = None) -> list[str]:
        ref = ref or self.default_branch
        return [
            commit.id
            for commit in self.gitlab_repo.commits.list(ref_name=ref, all=True)
        ]

    def get_file_content(self, path, ref=None) -> str:
        ref = ref or self.default_branch
        # GitLab cannot resolve './'
        path = os.path.normpath(path)
        try:
            file = self.gitlab_repo.files.get(file_path=path, ref=ref)
            return file.decode().decode()
        except gitlab.exceptions.GitlabGetError as ex:
            if ex.response_code == 404:
                raise FileNotFoundError(f"File '{path}' on {ref} not found") from ex
            raise GitlabAPIException() from ex

    def get_files(
        self,
        ref: Optional[str] = None,
        filter_regex: Optional[str] = None,
        recursive: bool = False,
    ) -> list[str]:
        ref = ref or self.default_branch
        paths = [
            file_dict["path"]
            for file_dict in self.gitlab_repo.repository_tree(
                ref=ref,
                recursive=recursive,
                all=True,
            )
            if file_dict["type"] != "tree"
        ]
        if filter_regex:
            paths = filter_paths(paths, filter_regex)

        return paths

    @indirect(GitlabIssue.get_list)
    def get_issue_list(
        self,
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list[Issue]:
        pass

    @indirect(GitlabIssue.get)
    def get_issue(self, issue_id: int) -> Issue:
        pass

    @indirect(GitlabIssue.create)
    def create_issue(
        self,
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> Issue:
        pass

    @indirect(GitlabPullRequest.get)
    def get_pr(self, pr_id: int) -> PullRequest:
        pass

    def get_tags(self) -> list["GitTag"]:
        tags = self.gitlab_repo.tags.list()
        return [GitTag(tag.name, tag.commit["id"]) for tag in tags]

    def _git_tag_from_tag_name(self, tag_name: str) -> GitTag:
        git_tag = self.gitlab_repo.tags.get(tag_name)
        return GitTag(name=git_tag.name, commit_sha=git_tag.commit["id"])

    @indirect(GitlabRelease.get_list)
    def get_releases(self) -> list[Release]:
        pass

    @indirect(GitlabRelease.get)
    def get_release(self, identifier=None, name=None, tag_name=None) -> GitlabRelease:
        pass

    @indirect(GitlabRelease.create)
    def create_release(
        self,
        tag: str,
        name: str,
        message: str,
        commit_sha: Optional[str] = None,
    ) -> GitlabRelease:
        pass

    @indirect(GitlabRelease.get_latest)
    def get_latest_release(self) -> Optional[GitlabRelease]:
        pass

    def list_labels(self):
        """
        Get list of labels in the repository.

        Returns:
            List of labels in the repository.
        """
        return list(self.gitlab_repo.labels.list())

    def get_forks(self) -> list["GitlabProject"]:
        try:
            forks = self.gitlab_repo.forks.list()
        except KeyError as ex:
            # > item = self._data[self._current]
            # > KeyError: 0
            # looks like some API weirdness
            raise OperationNotSupported(
                "Please upgrade python-gitlab to a newer version.",
            ) from ex
        return [
            GitlabProject(
                repo=fork.path,
                namespace=fork.namespace["full_path"],
                service=self.service,
            )
            for fork in forks
        ]

    def update_labels(self, labels):
        """
        Update the labels of the repository. (No deletion, only add not existing ones.)

        Args:
            labels: List of labels to be added.

        Returns:
            Number of added labels.
        """
        current_label_names = [la.name for la in list(self.gitlab_repo.labels.list())]
        changes = 0
        for label in labels:
            if label.name not in current_label_names:
                color = self._normalize_label_color(color=label.color)
                self.gitlab_repo.labels.create(
                    {
                        "name": label.name,
                        "color": color,
                        "description": label.description or "",
                    },
                )

                changes += 1
        return changes

    @staticmethod
    def _normalize_label_color(color):
        if not color.startswith("#"):
            return f"#{color}"
        return color

    def get_web_url(self) -> str:
        return self.gitlab_repo.web_url

    def get_sha_from_branch(self, branch: str) -> Optional[str]:
        try:
            return self.gitlab_repo.branches.get(branch).attributes["commit"]["id"]
        except GitlabGetError as ex:
            if ex.response_code == 404:
                return None
            raise GitlabAPIException from ex

    def get_contributors(self) -> set[str]:
        """
        Returns:
            Unique authors of the commits in the project.
        """

        def format_contributor(contributor: dict[str, Any]) -> str:
            return f"{contributor['name']} <{contributor['email']}>"

        return set(
            map(format_contributor, self.gitlab_repo.repository_contributors(all=True)),
        )

    def users_with_write_access(self) -> set[str]:
        return set(
            self._get_collaborators_with_given_access(
                access_levels=[
                    gitlab.const.DEVELOPER_ACCESS,
                    gitlab.const.MAINTAINER_ACCESS,
                    gitlab.const.OWNER_ACCESS,
                ],
            ),
        )

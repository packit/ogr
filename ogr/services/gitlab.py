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

import gitlab

from typing import List, Optional

from ogr.abstract import (
    GitService,
    GitUser,
    PullRequest,
    Issue,
    Release,
    IssueComment,
    PRComment,
    GitTag,
    IssueStatus,
)
from ogr.utils import (
    clone_repo_and_cd_inside,
    set_upstream_remote,
    set_origin_remote,
    fetch_all,
)

from ogr.services.base import BaseGitProject, BaseGitUser

logger = logging.getLogger(__name__)


class GitlabRelease(Release):
    project: "GitlabProject"

    def __init__(
        self,
        tag_name: str,
        url: Optional[str],
        created_at: str,
        tarball_url: str,
        git_tag: GitTag,
        project: "GitlabProject",
        raw_release,
    ) -> None:
        super().__init__(tag_name, url, created_at, tarball_url, git_tag, project)
        self.raw_release = raw_release

    @property
    def title(self):
        return self.raw_release.name

    @property
    def body(self):
        return self.raw_release.description


class GitlabService(GitService):
    name = "gitlab"

    def __init__(self, token=None, url=None, full_repo_name=None, ssl_verify=True):
        super().__init__(token=token)
        url = url or "https://gitlab.com"
        self.g = gitlab.Gitlab(url=url, private_token=token, ssl_verify=ssl_verify)
        self.g.auth()
        self.repo = None
        if full_repo_name:
            self.repo = self.g.projects.get(full_repo_name)

    @property
    def user(self) -> GitUser:
        return GitlabUser(service=self)

    def get_project(
        self, repo=None, namespace=None, is_fork=False, **kwargs
    ) -> "GitlabProject":
        if is_fork:
            namespace = self.user.get_username()
        return GitlabProject(repo=repo, namespace=namespace, service=self, **kwargs)

    @classmethod
    def create_from_remote_url(cls, remote_url, **kwargs):
        """ create instance of service from provided remote_url """
        raise NotImplementedError()

    @staticmethod
    def is_fork_of(user_repo, target_repo):
        """ is provided repo fork of the {parent_repo}/? """
        return user_repo.forked_from_project["id"] == target_repo.id

    def fork(self, target_repo):
        target_repo_org, target_repo_name = target_repo.split("/", 1)

        target_repo_gl = self.g.projects.get(target_repo)

        try:
            # is it already forked?
            user_repo = self.g.projects.get(
                "{}/{}".format(self.user.get_username(), target_repo_name)
            )
            if not self.is_fork_of(user_repo, target_repo_gl):
                raise RuntimeError(
                    "repo %s is not a fork of %s" % (user_repo, target_repo_gl)
                )
        except Exception:
            # nope
            user_repo = None

        if self.user.get_username() == target_repo_org:
            # user wants to fork its own repo; let's just set up remotes 'n stuff
            if not user_repo:
                raise RuntimeError("repo %s not found" % target_repo_name)
            clone_repo_and_cd_inside(
                user_repo.path, user_repo.attributes["ssh_url_to_repo"], target_repo_org
            )
        else:
            user_repo = user_repo or self._fork_gracefully(target_repo_gl)

            clone_repo_and_cd_inside(
                user_repo.path, user_repo.attributes["ssh_url_to_repo"], target_repo_org
            )

            set_upstream_remote(
                clone_url=target_repo_gl.attributes["http_url_to_repo"],
                ssh_url=target_repo_gl.attributes["ssh_url_to_repo"],
                pull_merge_name="merge-requests",
            )
        set_origin_remote(
            user_repo.attributes["ssh_url_to_repo"], pull_merge_name="merge-requests"
        )
        fetch_all()

    @staticmethod
    def _fork_gracefully(target_repo):
        """ fork if not forked, return forked repo """
        try:
            logger.info("forking repo %s", target_repo)
            fork = target_repo.forks.create({})
        except gitlab.GitlabCreateError:
            logger.error("repo %s cannot be forked" % target_repo)
            raise RuntimeError("repo %s not found" % target_repo)

        return fork

    def update_labels(self, labels):
        """
        Update the labels of the repository. (No deletion, only add not existing ones.)

        :param labels: [str]
        :return: int - number of added labels
        """
        current_label_names = [l.name for l in list(self.repo.labels.list())]
        changes = 0
        for label in labels:
            if label.name not in current_label_names:
                color = self._normalize_label_color(color=label.color)
                self.repo.labels.create(
                    {
                        "name": label.name,
                        "color": color,
                        "description": label.description or "",
                    }
                )

                changes += 1
        return changes

    @staticmethod
    def _normalize_label_color(color):
        if not color.startswith("#"):
            return "#{}".format(color)
        return color


class GitlabProject(BaseGitProject):
    service: GitlabService

    def __init__(
        self, repo: str, service: GitlabService, namespace: str, **unprocess_kwargs
    ) -> None:
        if unprocess_kwargs:
            logger.warning(
                f"GitlabProject will not process these kwargs: {unprocess_kwargs}"
            )
        super().__init__(repo, service, namespace)
        self.gitlab_repo = self.service.g.projects.get(f"{self.namespace}/{self.repo}")

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

    def get_branches(self) -> List[str]:
        return [branch.name for branch in self.gitlab_repo.branches.list()]

    def get_file_content(self, path, ref="master") -> str:
        try:
            file = self.gitlab_repo.files.get(file_path=path, ref=ref)
            return str(file.decode())
        except gitlab.exceptions.GitlabGetError as ex:
            raise FileNotFoundError(f"File '{path}' on {ref} not found", ex)

    @staticmethod
    def _issue_from_gitlab_object(gitlab_issue) -> Issue:
        return Issue(
            title=gitlab_issue.title,
            id=gitlab_issue.iid,
            url=gitlab_issue.web_url,
            description=gitlab_issue.description,
            status=gitlab_issue.state,
            author=gitlab_issue.author["username"],
            created=gitlab_issue.created_at,
        )

    @staticmethod
    def _issuecomment_from_gitlab_object(raw_comment) -> IssueComment:
        return IssueComment(
            comment=raw_comment.body,
            author=raw_comment.author["username"],
            created=raw_comment.created_at,
            edited=raw_comment.updated_at,
        )

    @staticmethod
    def _pr_from_gitlab_object(gitlab_pr) -> PullRequest:
        return PullRequest(
            title=gitlab_pr.title,
            id=gitlab_pr.iid,
            status=gitlab_pr.state,
            url=gitlab_pr.web_url,
            description=gitlab_pr.description,
            author=gitlab_pr.author["username"],
            source_branch=gitlab_pr.source_branch,
            target_branch=gitlab_pr.target_branch,
            created=gitlab_pr.created_at,
        )

    @staticmethod
    def _prcomment_from_gitlab_object(raw_comment) -> PRComment:
        return PRComment(
            comment=raw_comment.body,
            author=raw_comment.author["username"],
            created=raw_comment.created_at,
            edited=raw_comment.updated_at,
        )

    def _release_from_gitlab_object(
        self, raw_release, git_tag: GitTag
    ) -> GitlabRelease:
        return GitlabRelease(
            tag_name=raw_release.tag_name,
            url=None,
            created_at=raw_release.created_at,
            tarball_url=raw_release.assets["sources"][1]["url"],
            git_tag=git_tag,
            project=self,
            raw_release=raw_release,
        )

    def get_issue_list(self, status: IssueStatus = None) -> List[Issue]:
        issues = self.gitlab_repo.issues.list(
            state="opened", order_by="updated_at", sort="desc"
        )
        return [self._issue_from_gitlab_object(issue) for issue in issues]

    def get_issue_info(self, issue_id: int) -> Issue:
        issue = self.gitlab_repo.issues.get(issue_id)
        return self._issue_from_gitlab_object(gitlab_issue=issue)

    def create_issue(self, title: str, description: str) -> Issue:
        issue = self.gitlab_repo.issues.create(
            {"title": title, "description": description}
        )
        return self._issue_from_gitlab_object(issue)

    def close_issue(self, issue_id: int) -> Issue:
        issue = self.gitlab_repo.issues.get(issue_id)
        issue.state_event = "close"
        issue.save()
        return self._issue_from_gitlab_object(issue)

    def _get_all_issue_comments(self, issue_id: int) -> List[IssueComment]:
        issue = self.gitlab_repo.issues.get(issue_id)
        return [
            self._issuecomment_from_gitlab_object(raw_comment)
            for raw_comment in issue.notes.list()
        ]

    def issue_comment(self, issue_id: int, body: str) -> IssueComment:
        """
        Create comment on an issue.
        """
        issue = self.gitlab_repo.issues.get(issue_id)
        comment = issue.notes.create({"body": body})
        return self._issuecomment_from_gitlab_object(comment)

    def get_pr_info(self, pr_id: int) -> PullRequest:
        mr = self.gitlab_repo.mergerequests.get(pr_id)
        return self._pr_from_gitlab_object(mr)

    def list_pull_requests(self) -> List[PullRequest]:
        mrs = self.gitlab_repo.mergerequests.list(order_by="updated_at", sort="desc")
        return [self._pr_from_gitlab_object(mr) for mr in mrs]

    def create_pr(
        self, source_branch: str, target_branch: str, title: str, labels: List[str]
    ) -> PullRequest:
        mr = self.gitlab_repo.mergerequests.create(
            {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "labels": labels,
            }
        )
        return self._pr_from_gitlab_object(mr)

    def update_pr_info(self, pr_id: int, description: str) -> PullRequest:
        pr = self.gitlab_repo.mergerequests.get(pr_id)
        pr.description = description
        pr.save()
        return self._pr_from_gitlab_object(pr)

    def get_all_pr_commits(self, pr_id: int) -> List[str]:
        mr = self.gitlab_repo.mergerequests.get(pr_id)
        return [commit.id for commit in mr.commits()]

    def _get_all_pr_comments(self, pr_id: int) -> List[PRComment]:
        pr = self.gitlab_repo.mergerequests.get(pr_id)
        return [
            self._prcomment_from_gitlab_object(raw_comment)
            for raw_comment in pr.notes.list()
        ]

    def pr_comment(
        self,
        pr_id: int,
        body: str,
        commit: str = None,
        filename: str = None,
        row: int = None,
    ) -> PRComment:
        """
        Create comment on an pr.
        """
        pr = self.gitlab_repo.issues.get(pr_id)
        comment = pr.notes.create({"body": body})
        return self._prcomment_from_gitlab_object(comment)

    def get_tags(self) -> List["GitTag"]:
        tags = self.gitlab_repo.tags.list()
        return [GitTag(tag.name, tag.commit["id"]) for tag in tags]

    def _git_tag_from_tag_name(self, tag_name: str) -> GitTag:
        git_tag = self.gitlab_repo.tags.get(tag_name)
        return GitTag(name=git_tag.name, commit_sha=git_tag.commit["id"])

    def get_releases(self) -> List[Release]:
        releases = self.gitlab_repo.releases.list()
        return [
            self._release_from_gitlab_object(
                raw_release=release,
                git_tag=self._git_tag_from_tag_name(release.tag_name),
            )
            for release in releases
        ]

    def get_release(self, identifier=None, name=None, tag_name=None) -> GitlabRelease:
        release = self.gitlab_repo.releases.get(tag_name)
        return self._release_from_gitlab_object(
            raw_release=release, git_tag=self._git_tag_from_tag_name(release.tag_name)
        )

    def create_release(
        self, name: str, tag_name: str, description: str, ref=None
    ) -> GitlabRelease:
        release = self.gitlab_repo.releases.create(
            {"name": name, "tag_name": tag_name, "description": description, "ref": ref}
        )
        return self._release_from_gitlab_object(
            raw_release=release, git_tag=self._git_tag_from_tag_name(release.tag_name)
        )

    def list_labels(self):
        """
        Get list of labels in the repository.
        :return: [Label]
        """
        return list(self.gitlab_repo.labels.list())

    def get_forks(self) -> List["GitlabProject"]:
        """
        Get forks of the project.

        :return: [GitlabProject]
        """
        fork_objects = [
            GitlabProject(
                repo=fork.path,
                namespace=fork.namespace["full_path"],
                service=self.service,
            )
            for fork in self.gitlab_repo.forks.list()
        ]
        return fork_objects


class GitlabUser(BaseGitUser):
    service: GitlabService

    def __init__(self, service: GitlabService) -> None:
        super().__init__(service=service)

    def __str__(self) -> str:
        return f'Gitlab(username="{self.get_username()}")'

    @property
    def _gitlab_user(self):
        return self.service.g.user

    def get_username(self) -> str:
        return self._gitlab_user.username

    def get_email(self) -> str:
        return self._gitlab_user.email

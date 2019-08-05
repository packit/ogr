import os
import unittest

from ogr import PagureService
from ogr.abstract import PRStatus, IssueStatus
from ogr.exceptions import PagureAPIException
from ogr.persistent_storage import PersistentObjectStorage

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class PagureTests(unittest.TestCase):
    def setUp(self):
        self.token = os.environ.get("PAGURE_TOKEN")
        self.user = os.environ.get("PAGURE_USER")
        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_pagure_data_{test_name}.yaml"
        )

        PersistentObjectStorage().storage_file = persistent_data_file

        if PersistentObjectStorage().is_write_mode and (
            not self.user or not self.token
        ):
            raise EnvironmentError("please set PAGURE_TOKEN PAGURE_USER env variables")

        self.service = PagureService(token=self.token)
        self.docker_py_project = self.service.get_project(
            namespace="rpms", repo="python-docker", username="lachmanfrantisek"
        )
        self.abiword_project = self.service.get_project(
            namespace="rpms", repo="abiword", username="churchyard"
        )
        self.abiword_fork = self.service.get_project(
            namespace="rpms", repo="abiword", username="churchyard", is_fork=True
        )

        self.service_pagure = PagureService(
            token=self.token, instance_url="https://pagure.io"
        )
        self.ogr_test_project = self.service_pagure.get_project(
            namespace=None, repo="ogr-test", username="marusinm"
        )

    def tearDown(self):
        self.service.persistent_storage.dump()


class Comments(PagureTests):
    def test_issue_comments(self):
        issue_comments = self.ogr_test_project._get_all_issue_comments(2)
        assert issue_comments
        assert len(issue_comments) == 4
        assert issue_comments[0].comment.startswith("this is")

    def test_pr_comments(self):
        pr_comments = self.abiword_project.get_pr_comments(1)
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[0].comment.startswith("rebased")

    def test_pr_comments_reversed(self):
        pr_comments = self.abiword_project.get_pr_comments(1, reverse=True)
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[1].comment.startswith("rebased")

    def test_pr_comments_filter(self):
        pr_comments = self.abiword_project.get_pr_comments(1, filter_regex="rebased")
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].comment.startswith("rebased")

        pr_comments = self.abiword_project.get_pr_comments(
            1, filter_regex="onto ([a-z0-9]*)"
        )
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].comment.startswith("rebased")

    def test_pr_comments_search(self):
        comment_match = self.abiword_project.search_in_pr(1, filter_regex="rebased")
        assert comment_match
        assert comment_match[0] == "rebased"

        comment_match = self.abiword_project.search_in_pr(
            1, filter_regex="onto ([a-z0-9]*)"
        )
        assert comment_match
        assert comment_match[0].startswith("onto")
        assert comment_match[1].startswith("09ac068")


class GenericCommands(PagureTests):
    def test_description(self):
        description = self.docker_py_project.get_description()
        assert description == "The python-docker rpms"

    def test_branches(self):
        branches = self.docker_py_project.get_branches()
        assert branches
        assert set(branches) == {"f26", "f27", "f28", "f29", "f30", "master"}

    def test_get_releases(self):
        releases = self.ogr_test_project.get_releases()
        assert releases

        assert len(releases) >= 2

    def test_git_urls(self):
        urls = self.docker_py_project.get_git_urls()
        assert urls
        assert len(urls) == 2
        assert "git" in urls
        assert "ssh" in urls
        assert urls["git"] == "https://src.fedoraproject.org/rpms/python-docker.git"
        assert urls["ssh"].endswith("@pkgs.fedoraproject.org/rpms/python-docker.git")

    def test_username(self):
        # changed to check just lenght, because it is based who regenerated data files
        assert len(self.service.user.get_username()) > 3

    def test_get_file(self):
        file_content = self.docker_py_project.get_file_content(".gitignore")
        assert file_content
        assert isinstance(file_content, str)
        assert "docker-2.6.1.tar.gz" in file_content

    def test_nonexisting_file(self):
        with self.assertRaises(Exception) as _:
            self.docker_py_project.get_file_content(".blablabla_nonexisting_file")

    def test_parent_project(self):
        assert self.abiword_fork.parent.namespace == "rpms"
        assert self.abiword_fork.parent.repo == "abiword"

    def test_commit_statuses(self):
        flags = self.abiword_project.get_commit_statuses(
            commit="d87466de81c72231906a6597758f37f28830bb71"
        )
        assert isinstance(flags, list)
        assert len(flags) == 0

    def test_get_owners(self):
        owners = self.ogr_test_project.get_owners()
        assert ["marusinm"] == owners

    def test_issue_permissions(self):
        owners = self.ogr_test_project.who_can_close_issue()
        assert "marusinm" in owners

        issue = self.ogr_test_project.get_issue_info(1)
        assert self.ogr_test_project.can_close_issue("marusinm", issue)

    def test_pr_permissions(self):
        owners = self.ogr_test_project.who_can_merge_pr()
        assert "marusinm" in owners
        assert self.ogr_test_project.can_merge_pr("marusinm")


class Issues(PagureTests):
    def test_issue_list(self):
        issue_list = self.ogr_test_project.get_issue_list()
        assert isinstance(issue_list, list)

        issue_list = self.ogr_test_project.get_issue_list(status=IssueStatus.all)
        assert issue_list
        assert len(issue_list) >= 9

    def test_issue_info(self):
        issue_info = self.ogr_test_project.get_issue_info(issue_id=1)
        assert issue_info
        assert issue_info.title.startswith("test1")
        assert issue_info.status == IssueStatus.closed


class PullRequests(PagureTests):
    def test_pr_list(self):
        pr_list = self.abiword_project.get_pr_list()
        assert isinstance(pr_list, list)
        assert not pr_list

        pr_list = self.abiword_project.get_pr_list(status=PRStatus.all)
        assert pr_list
        assert len(pr_list) == 2

    def test_pr_info(self):
        pr_info = self.abiword_project.get_pr_info(pr_id=1)
        assert pr_info
        assert pr_info.title.startswith("Update Python 2 dependency")
        assert pr_info.status == PRStatus.merged

    @unittest.skip("No TOKEN is able to do it for now.")
    def test_update_pr_info(self):
        packit_prject = self.service.get_project(namespace="rpms", repo="packit")

        pr_id = 1
        packit_prject.update_pr_info(
            pr_id=pr_id, title="changed", description="changed description"
        )
        pr_info = packit_prject.get_pr_info(pr_id=pr_id)
        assert pr_info.title == "changed"
        assert pr_info.description == "changed description"

        packit_prject.update_pr_info(
            pr_id=pr_id, title="new", description="new description"
        )
        pr_info = packit_prject.get_pr_info(pr_id=pr_id)
        assert pr_info.title == "new"
        assert pr_info.description == "new description"


class Forks(PagureTests):
    def test_fork(self):
        assert self.abiword_fork.exists()
        assert self.abiword_fork.is_fork
        fork_description = self.abiword_fork.get_description()
        assert fork_description
        a = self.abiword_fork.parent
        assert a
        is_forked = a.is_forked()
        assert is_forked and isinstance(is_forked, bool)
        fork = a.get_fork(create=False)
        assert fork
        assert fork.is_fork
        urls = fork.get_git_urls()
        assert "{username}" not in urls["ssh"]

    def test_nonexisting_fork(self):
        abiword_project_non_existing_fork = self.service.get_project(
            namespace="rpms",
            repo="abiword",
            username="qwertzuiopasdfghjkl",
            is_fork=True,
        )
        assert not abiword_project_non_existing_fork.exists()
        with self.assertRaises(PagureAPIException) as ex:
            abiword_project_non_existing_fork.get_description()
        assert "Project not found" in ex.exception.pagure_error

    def test_fork_property(self):
        fork = self.abiword_project.get_fork()
        assert fork
        assert fork.get_description()

    def test_create_fork(self):
        not_existing_fork = self.docker_py_project.get_fork(create=False)
        assert not not_existing_fork
        assert not self.docker_py_project.is_forked()

        old_forks = self.docker_py_project.service.user.get_forks()

        self.docker_py_project.fork_create()

        assert self.docker_py_project.get_fork().exists()
        assert self.docker_py_project.is_forked()

        new_forks = self.docker_py_project.service.user.get_forks()
        assert len(old_forks) == len(new_forks) - 1

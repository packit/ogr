import os
from pathlib import Path
import unittest
from ogr.services.github import GithubService
from requre.online_replacing import record_requests_for_all_methods
from requre.utils import get_datafile_filename


@record_requests_for_all_methods()
class ReadOnly(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.token = os.environ.get("GITHUB_TOKEN")
        if not Path(get_datafile_filename(obj=self)).exists() and not self.token:
            raise EnvironmentError(
                "You are in Requre write mode, please set proper GITHUB_TOKEN env variables"
            )
        self._service = None
        self._ogr_project = None

    @property
    def service(self):
        if not self._service:
            self._service = GithubService(token=self.token, read_only=True)
        return self._service

    @property
    def ogr_project(self):
        if not self._ogr_project:
            self._ogr_project = self.service.get_project(namespace="packit", repo="ogr")
        return self._ogr_project

    def test_pr_comments(self):
        pr_comments = self.ogr_project.get_pr(9).get_comments()
        assert pr_comments
        assert len(pr_comments) == 2

        assert pr_comments[0].body.endswith("fixed")
        assert pr_comments[1].body.startswith("LGTM")

    def test_create_pr(self):
        pr = self.ogr_project.create_pr(
            "title", "text", "master", "lbarcziova:testing_branch"
        )
        assert pr.title == "title"

    def test_create_fork(self):
        fork = self.ogr_project.fork_create()
        assert not fork.is_fork

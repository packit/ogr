import os
from requre.online_replacing import record_requests_for_all_methods
from requre.utils import get_datafile_filename
import unittest
from pathlib import Path
from ogr import GithubService, PagureService, get_project, GitlabService
from ogr.services.github import GithubProject
from ogr.services.gitlab import GitlabProject
from ogr.services.pagure import PagureProject


@record_requests_for_all_methods()
class FactoryTests(unittest.TestCase):
    def setUp(self):
        self._github_service = None
        self._pagure_service = None
        self._gitlab_service = None
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.pagure_token = os.environ.get("PAGURE_TOKEN")
        self.gitlab_token = os.environ.get("GITLAB_TOKEN") or "some_token"
        if not Path(get_datafile_filename(obj=self)).exists():
            if (
                not self.github_token
                or not self.pagure_token
                or not os.environ.get("GITLAB_TOKEN")
            ):
                raise EnvironmentError(
                    "You are in requre write mode, please set GITHUB_TOKEN PAGURE_TOKEN"
                    " GITLAB_TOKEN env variables"
                )

    @property
    def github_service(self):
        if not self._github_service:
            self._github_service = GithubService(token=self.github_token)
        return self._github_service

    @property
    def pagure_service(self):
        if not self._pagure_service:
            self._pagure_service = PagureService(token=self.pagure_token)
        return self._pagure_service

    @property
    def gitlab_service(self):
        if not self._gitlab_service:
            self._gitlab_service = GitlabService(
                token=self.gitlab_token, instance_url="https://gitlab.com"
            )
        return self._gitlab_service

    @property
    def custom_instances(self):
        return [
            self.github_service,
            self.pagure_service,
            self.gitlab_service,
        ]

    def test_get_project_github(self):
        # unittest + pytest is a no-no for fixtures/parametrize
        urls = [
            "https://github.com/packit/ogr",
            "git@github.com:TomasTomecek/speaks.git",
        ]
        for url in urls:
            project = get_project(url=url, custom_instances=self.custom_instances)
            assert isinstance(project, GithubProject)
            assert project.github_repo

    def test_get_project_pagure(self):
        project = get_project(
            url="https://src.fedoraproject.org/rpms/python-ogr",
            custom_instances=self.custom_instances,
        )
        assert isinstance(project, PagureProject)
        assert project.exists()

    def test_get_project_gitlab(self):
        project = get_project(
            url="https://gitlab.com/packit-service/ogr-tests",
            custom_instances=self.custom_instances,
        )
        assert isinstance(project, GitlabProject)
        assert project.gitlab_repo

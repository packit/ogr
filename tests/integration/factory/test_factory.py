# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import os
import unittest
from pathlib import Path

from requre.helpers import record_httpx
from requre.online_replacing import record_requests_for_all_methods
from requre.utils import get_datafile_filename

from ogr import ForgejoService, GithubService, GitlabService, PagureService, get_project
from ogr.services.forgejo import ForgejoProject
from ogr.services.github import GithubProject
from ogr.services.gitlab import GitlabProject
from ogr.services.pagure import PagureProject


@record_httpx()
@record_requests_for_all_methods()
class FactoryTests(unittest.TestCase):
    def setUp(self):
        self._github_service = None
        self._pagure_service = None
        self._gitlab_service = None
        self._forgejo_service = None
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.pagure_token = os.environ.get("PAGURE_TOKEN")
        self.gitlab_token = os.environ.get("GITLAB_TOKEN") or "some_token"
        self.forgejo_token = os.environ.get("FORGEJO_TOKEN")
        if not Path(get_datafile_filename(obj=self)).exists() and (
            not self.github_token
            and not self.pagure_token
            and not os.environ.get("GITLAB_TOKEN")
            and not self.forgejo_token
        ):
            raise OSError(
                "You are in requre write mode, please set GITHUB_TOKEN PAGURE_TOKEN"
                " GITLAB_TOKEN FORGEJO_TOKEN env variables",
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
                token=self.gitlab_token,
                instance_url="https://gitlab.com",
            )
        return self._gitlab_service

    @property
    def forgejo_service(self):
        if not self._forgejo_service:
            self._forgejo_service = ForgejoService(
                instance_url="https://v10.next.forgejo.org",  # a test server
                api_key=self.forgejo_token,
            )
        return self._forgejo_service

    @property
    def custom_instances(self):
        return [
            self.github_service,
            self.pagure_service,
            self.gitlab_service,
            self.forgejo_service,
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

    def test_get_project_forgejo(self):
        project = get_project(
            url="https://v10.next.forgejo.org/packit/test",
            custom_instances=self.custom_instances,
        )
        assert isinstance(project, ForgejoProject)
        assert project.forgejo_repo

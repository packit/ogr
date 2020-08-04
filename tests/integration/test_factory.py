import os

from requre import RequreTestCase
from requre.storage import PersistentObjectStorage
from requre.utils import StorageMode

from ogr import GithubService, PagureService, get_project, GitlabService
from ogr.services.github import GithubProject
from ogr.services.gitlab import GitlabProject
from ogr.services.pagure import PagureProject


class FactoryTests(RequreTestCase):
    def setUp(self):
        super().setUp()
        print(PersistentObjectStorage().storage_file)
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.pagure_token = os.environ.get("PAGURE_TOKEN")
        self.gitlab_token = os.environ.get("GITLAB_TOKEN") or "some_token"

        if PersistentObjectStorage().mode == StorageMode.write:
            if not self.github_token:
                raise EnvironmentError(
                    "You are in requre write mode, please set GITHUB_TOKEN env variables"
                )
            if not self.pagure_token:
                raise EnvironmentError(
                    "You are in requre write mode, please set PAGURE_TOKEN env variables"
                )
            if not os.environ.get("GITLAB_TOKEN"):
                raise EnvironmentError(
                    "You are in requre write mode, please set GITLAB_TOKEN env variables"
                )

        self.github_service = GithubService(token=self.github_token)
        self.pagure_service = PagureService(token=self.pagure_token)
        self.gitlab_service = GitlabService(
            token=self.gitlab_token, instance_url="https://gitlab.com"
        )
        self.custom_instances = [
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

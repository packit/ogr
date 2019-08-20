import os
import unittest

from ogr import GithubService, PagureService, get_project, GitlabService
from ogr.persistent_storage import PersistentObjectStorage
from ogr.services.github import GithubProject
from ogr.services.gitlab import GitlabProject
from ogr.services.pagure import PagureProject

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_user = os.environ.get("GITHUB_USER")
        self.pagure_token = os.environ.get("PAGURE_TOKEN")
        self.pagure_user = os.environ.get("PAGURE_USER")
        self.gitlab_token = os.environ.get("GITLAB_TOKEN") or "some_token"
        self.gitlab_user = os.environ.get("GITLAB_USER")

        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_factory_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file

        if PersistentObjectStorage().is_write_mode and (
            not self.github_user or not self.github_token
        ):
            raise EnvironmentError("please set GITHUB_TOKEN GITHUB_USER env variables")

        if PersistentObjectStorage().is_write_mode and (
            not self.pagure_user or not self.pagure_token
        ):
            raise EnvironmentError("please set PAGURE_TOKEN PAGURE_USER env variables")

        self.github_service = GithubService(token=self.github_token)
        self.pagure_service = PagureService(token=self.pagure_token)
        self.gitlab_service = GitlabService(
            token=self.gitlab_token, instance_url="https://gitlab.gnome.org"
        )
        self.custom_instances = [
            self.github_service,
            self.pagure_service,
            self.gitlab_service,
        ]

    def tearDown(self):
        PersistentObjectStorage().dump()

    def test_get_project_github(self):
        project = get_project(
            url="https://github.com/packit-service/ogr",
            custom_instances=self.custom_instances,
        )
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
            url="https://gitlab.gnome.org/lbarcziova/testing-ogr-repo",
            custom_instances=self.custom_instances,
        )
        assert isinstance(project, GitlabProject)
        assert project.gitlab_repo

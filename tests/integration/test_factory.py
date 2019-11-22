import os
import unittest

from ogr import GithubService, PagureService, get_project, GitlabService
from requre.storage import PersistentObjectStorage
from requre.utils import StorageMode
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
        self.pagure_token = os.environ.get("PAGURE_TOKEN")
        self.gitlab_token = os.environ.get("GITLAB_TOKEN") or "some_token"

        test_name = self.id() or "all"

        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_factory_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file

        if (
            PersistentObjectStorage().mode == StorageMode.write
            and not self.github_token
        ):
            raise EnvironmentError("please set GITHUB_TOKEN env variables")

        if (
            PersistentObjectStorage().mode == StorageMode.write
            and not self.pagure_token
        ):
            raise EnvironmentError("please set PAGURE_TOKEN env variables")

        if PersistentObjectStorage() == StorageMode.write and not os.environ.get(
            "GITLAB_TOKEN"
        ):
            raise EnvironmentError("please set GITLAB_TOKEN env variables")

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
            url="https://gitlab.com/packit-service/ogr-tests",
            custom_instances=self.custom_instances,
        )
        assert isinstance(project, GitlabProject)
        assert project.gitlab_repo

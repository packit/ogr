import os
from pathlib import Path
import unittest

from requre.utils import get_datafile_filename

from ogr import GithubService


class GithubTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.token = os.environ.get("GITHUB_TOKEN")
        if not Path(get_datafile_filename(obj=self)).exists() and not self.token:
            raise EnvironmentError(
                "You are in Requre write mode, please set proper GITHUB_TOKEN env variables"
            )
        self._service = None
        self._ogr_project = None
        self._ogr_fork = None
        self._hello_world_project = None
        self._not_forked_project = None

    @property
    def service(self):
        if not self._service:
            self._service = GithubService(token=self.token)
        return self._service

    @property
    def ogr_project(self):
        if not self._ogr_project:
            self._ogr_project = self.service.get_project(namespace="packit", repo="ogr")
        return self._ogr_project

    @property
    def ogr_fork(self):
        if not self._ogr_fork:
            self._ogr_fork = self.service.get_project(
                namespace="packit", repo="ogr", is_fork=True
            )
        return self._ogr_fork

    @property
    def hello_world_project(self):
        if not self._hello_world_project:
            self._hello_world_project = self.service.get_project(
                namespace="packit", repo="hello-world"
            )
        return self._hello_world_project

    @property
    def not_forked_project(self):
        if not self._not_forked_project:
            self._not_forked_project = self.service.get_project(
                namespace="fedora-modularity", repo="fed-to-brew"
            )
        return self._not_forked_project

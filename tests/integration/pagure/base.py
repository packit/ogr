import os
import unittest

from requre.utils import get_datafile_filename

from ogr import PagureService


class PagureTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.token = os.environ.get("PAGURE_TOKEN")

        if not get_datafile_filename(obj=self) and (not self.token):
            raise EnvironmentError(
                "You are in Requre write mode, please set PAGURE_TOKEN env variables"
            )
        self._service = None
        self._user = None
        self._ogr_project = None
        self._ogr_fork = None

    @property
    def service(self):
        if not self._service:
            self._service = PagureService(
                token=self.token, instance_url="https://pagure.io"
            )
        return self._service

    @property
    def user(self):
        if not self._user:
            self._user = self.service.user.get_username()
        return self._user

    @property
    def ogr_project(self):
        if not self._ogr_project:
            self._ogr_project = self.service.get_project(
                namespace=None, repo="ogr-tests"
            )
        return self._ogr_project

    @property
    def ogr_fork(self):
        if not self._ogr_fork:
            self._ogr_fork = self.service.get_project(
                namespace=None, repo="ogr-tests", username=self.user, is_fork=True
            )
        return self._ogr_fork

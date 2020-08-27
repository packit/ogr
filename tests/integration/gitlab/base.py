import os
from pathlib import Path
import unittest

from requre.utils import get_datafile_filename

from ogr.services.gitlab import GitlabService


class GitlabTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.token = os.environ.get("GITLAB_TOKEN")

        if not Path(get_datafile_filename(obj=self)).exists() and not self.token:
            raise EnvironmentError(
                "You are in Requre write mode, please set GITLAB_TOKEN env variables"
            )
        elif not self.token:
            self.token = "some_token"
        self._service = None
        self._project = None

    @property
    def service(self):
        if not self._service:
            self._service = GitlabService(
                token=self.token, instance_url="https://gitlab.com", ssl_verify=True
            )
        return self._service

    @property
    def project(self):
        if not self._project:
            self._project = self.service.get_project(
                repo="ogr-tests", namespace="packit-service"
            )
        return self._project

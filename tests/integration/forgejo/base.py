# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import os
import unittest
from pathlib import Path

from requre.utils import get_datafile_filename

from ogr import ForgejoService


class ForgejoTests(unittest.TestCase):
    def setUp(self):
        self._service = None
        self._project = None
        self._token = os.environ.get("FORGEJO_TOKEN")
        if not Path(get_datafile_filename(obj=self)).exists() and (not self._token):
            raise OSError(
                "You are in requre write mode, please set FORGEJO_TOKEN env variable",
            )

    @property
    def service(self):
        if not self._service:
            self._service = ForgejoService(
                instance_url="https://v10.next.forgejo.org",  # a test server
                api_key=self._token,
            )
        return self._service

    @property
    def project(self):
        if not self._project:
            self._project = self.service.get_project(
                repo="ogr-tests",
                namespace="manky201",
            )
        return self._project

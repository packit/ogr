# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import os
import unittest
from pathlib import Path

from requre.utils import get_datafile_filename

from ogr import ForgejoService


class ForgejoTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.api_key = os.environ.get("FORGEJO_TOKEN")

        if not Path(get_datafile_filename(obj=self)).exists() and not self.api_key:
            raise OSError(
                "You are in Requre write mode, please set FORGEJO_TOKEN env variables",
            )

        if not self.api_key:
            self.api_key = "some_token"

        self._service = None
        self._project = None

    @property
    def service(self):
        if not self._service:
            self._service = ForgejoService(
                api_key=self.api_key,
                instance_url="https://v10.next.forgejo.org",
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

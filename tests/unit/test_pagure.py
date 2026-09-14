# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from unittest import TestCase

from ogr import PagureService


class TestPagureService(TestCase):
    def test_hostname(self):
        assert PagureService().hostname == "pagure.io"
        assert (
            PagureService(instance_url="https://git.centos.org").hostname
            == "git.centos.org"
        )

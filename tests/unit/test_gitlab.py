# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from unittest import TestCase

from ogr import GitlabService


class TestGitlabService(TestCase):
    def test_hostname(self):
        assert GitlabService().hostname == "gitlab.com"
        assert (
            GitlabService(instance_url="https://gitlab.gnome.org").hostname
            == "gitlab.gnome.org"
        )

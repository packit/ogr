# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import os

import pytest

from ogr.services.forgejo import ForgejoService


@pytest.fixture
def service():
    api_key = os.environ.get("FORGEJO_TOKEN")
    return ForgejoService(
        instance_url="https://v10.next.forgejo.org",
        api_key=api_key,
    )

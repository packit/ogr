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


@pytest.fixture
def project(service):
    return service.get_project(
        namespace="packit-validator",
        repo="ogr-tests",
    )


@pytest.fixture
def hello_world_project(service):
    return service.get_project(
        namespace="packit-validator",
        repo="hello-world",
    )

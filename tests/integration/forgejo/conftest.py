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
    repo = os.environ.get("FORGEJO_REPO", "existing_repo_name")
    namespace = os.environ.get("FORGEJO_NAMESPACE", "existing_namespace")
    project = service.get_project(repo=repo, namespace=namespace)
    if not project:
        pytest.skip(f"Project {namespace}/{repo} does not exist.")
    return project

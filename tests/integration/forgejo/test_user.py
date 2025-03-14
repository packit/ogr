# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from requre.helpers import record_httpx


@record_httpx()
def test_get_email(service):
    assert service.user.get_email() == "public-repos-bot@packit.dev"


@record_httpx()
def test_get_projects(service):
    """When recording this test,
    run it after test_service.py which will create the repos.
    """
    projects = service.user.get_projects()
    assert len(projects) == 3
    namespaces = [project.namespace for project in projects]
    repos = [project.repo for project in projects]
    assert "packit" in namespaces
    assert "packit-validator" in namespaces
    assert "test" in repos
    assert "test_1" in repos


@record_httpx()
def test_get_forks(service):
    forks = service.user.get_forks()
    assert len(forks) == 0

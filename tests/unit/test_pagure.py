import pytest

from ogr.services.pagure import PagureService


@pytest.fixture()
def pagure_service():
    return PagureService(token="12345", instance_url="https://pagure.pagure")


@pytest.fixture()
def test_project(pagure_service):
    test_project = pagure_service.get_project(repo="my-test-project", namespace="rpms")
    return test_project


def test_repo(test_project):
    assert test_project.repo == "my-test-project"


def test_namespace(test_project):
    assert test_project.namespace == "rpms"


def test_full_repo_name(test_project):
    assert test_project.full_repo_name == "rpms/my-test-project"


def test_non_fork(pagure_service):
    test_project = pagure_service.get_project(repo="my-test-project", namespace="rpms")
    assert not test_project.is_fork
    assert "fork" not in test_project.full_repo_name


def test_fork(pagure_service):
    test_project = pagure_service.get_project(
        repo="my-test-project", namespace="rpms", is_fork=True, username="someone"
    )
    assert test_project.is_fork
    assert test_project.full_repo_name == "fork/someone/rpms/my-test-project"
    assert test_project.namespace == "fork/someone/rpms"

import pytest

from ogr.services.our_pagure import OurPagure


@pytest.fixture()
def pagure():
    return OurPagure(token="12345", instance_url="https://pagure.pagure")


@pytest.fixture()
def pagure_project():
    test_project = OurPagure(
        token="12345",
        instance_url="https://pagure.pagure",
        repo="my-test-project",
        namespace="rpms",
    )
    return test_project


@pytest.fixture()
def pagure_project_fork():
    test_project = OurPagure(
        token="12345",
        instance_url="https://pagure.pagure",
        repo="my-test-project",
        namespace="rpms",
        fork_username="somebody",
    )
    return test_project


def test_repo(pagure_project):
    assert pagure_project.repo_name == "my-test-project"
    assert pagure_project.repo == "rpms/my-test-project"


def test_repo_fork(pagure_project_fork):
    assert pagure_project_fork.repo_name == "my-test-project"
    assert pagure_project_fork.repo == "rpms/my-test-project"
    assert pagure_project_fork.username == "somebody"


def test_api_url(pagure):
    assert pagure.api_url == "https://pagure.pagure/api/0/"


@pytest.mark.parametrize(
    "args_list,result",
    [
        ([], "https://pagure.pagure/api/0/"),
        (["something"], "https://pagure.pagure/api/0/something"),
        (["a", "b", "c", "d"], "https://pagure.pagure/api/0/a/b/c/d"),
    ],
)
def test_get_api_url(pagure, args_list, result):
    assert pagure.get_api_url(*args_list) == result


@pytest.mark.parametrize(
    "args_list,result",
    [
        ([], "https://pagure.pagure/api/0/fork/somebody"),
        (["something"], "https://pagure.pagure/api/0/fork/somebody/something"),
        (["a", "b", "c", "d"], "https://pagure.pagure/api/0/fork/somebody/a/b/c/d"),
    ],
)
def test_get_api_url_fork(pagure_project_fork, args_list, result):
    assert pagure_project_fork.get_api_url(*args_list) == result


@pytest.mark.parametrize(
    "args_list,result",
    [
        ([], "https://pagure.pagure/api/0/"),
        (["something"], "https://pagure.pagure/api/0/something"),
        (["a", "b", "c", "d"], "https://pagure.pagure/api/0/a/b/c/d"),
    ],
)
def test_get_api_url_fork_ignore_fork(pagure_project_fork, args_list, result):
    assert pagure_project_fork.get_api_url(*args_list, add_fork=False) == result

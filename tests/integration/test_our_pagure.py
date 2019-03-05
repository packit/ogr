import os

import pytest

from ogr.services.our_pagure import OurPagure
from tests.integration.conftest import skipif_not_all_env_vars_set

pytestmark = skipif_not_all_env_vars_set(["PAGURE_TOKEN", "PAGURE_USER"])


@pytest.fixture()
def pagure_token():
    return os.environ["PAGURE_TOKEN"]


@pytest.fixture()
def pagure_user():
    return os.environ["PAGURE_USER"]


@pytest.fixture()
def pagure(pagure_token):
    return OurPagure(token=pagure_token, instance_url="https://src.fedoraproject.org")


@pytest.fixture()
def pagure_docker_py_project(pagure_token):
    docker_py = OurPagure(
        namespace="rpms",
        token=pagure_token,
        repo="python-docker-py",
        instance_url="https://src.fedoraproject.org",
    )
    return docker_py


@pytest.fixture()
def pagure_abiword_project(pagure_token):
    abiword = OurPagure(
        namespace="rpms",
        token=pagure_token,
        repo="abiword",
        instance_url="https://src.fedoraproject.org",
    )
    return abiword


@pytest.fixture()
def pagure_abiword_project_fork(pagure_token):
    abiword = OurPagure(
        namespace="rpms",
        token=pagure_token,
        repo="abiword",
        username="churchyard",
        instance_url="https://src.fedoraproject.org",
    )
    return abiword


@pytest.fixture()
def pagure_abiword_project_non_existing_fork(pagure_token):
    abiword = OurPagure(
        namespace="rpms",
        token=pagure_token,
        repo="abiword",
        username="someunexistingusernamethatshouldnotexist",
        instance_url="https://src.fedoraproject.org",
    )
    return abiword


def test_description(pagure_docker_py_project):
    description = pagure_docker_py_project.get_project_description()
    assert description == "The python-docker-py rpms"


def test_branches(pagure_docker_py_project):
    branches = pagure_docker_py_project.get_branches()
    assert branches
    assert branches == [
        "el6",
        "epel7",
        "f19",
        "f20",
        "f21",
        "f22",
        "f23",
        "f24",
        "f25",
        "f26",
        "f27",
        "f28",
        "master",
        "private-ttomecek-push-to-tls-registries-without-auth",
    ]


def test_git_urls(pagure_docker_py_project):
    urls = pagure_docker_py_project.get_git_urls()
    assert urls
    assert len(urls) == 2
    assert "git" in urls
    assert "ssh" in urls
    assert urls["git"] == "https://src.fedoraproject.org/rpms/python-docker-py.git"
    assert urls["ssh"].endswith("@pkgs.fedoraproject.org/rpms/python-docker-py.git")


def test_pr_list(pagure_abiword_project):
    pr_list = pagure_abiword_project.list_requests()
    assert isinstance(pr_list, list)
    assert not pr_list

    pr_list = pagure_abiword_project.list_requests(status="All")
    assert pr_list
    assert len(pr_list) == 2


def test_pr_info(pagure_abiword_project):
    pr_info = pagure_abiword_project.request_info(request_id=1)
    assert pr_info
    assert pr_info["title"].startswith("Update Python 2 dependency")
    assert pr_info["status"] == "Merged"


def test_commit_flags(pagure_abiword_project):
    flags = pagure_abiword_project.get_commit_flags(
        commit="d87466de81c72231906a6597758f37f28830bb71"
    )
    assert isinstance(flags, list)
    assert len(flags) == 0


def test_username(pagure, pagure_user):
    assert pagure.whoami() == pagure_user

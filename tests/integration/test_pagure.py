import os

import pytest
from libpagure import APIError

from ogr.abstract import PRStatus
from ogr.services.pagure import PagureService
from tests.integration.conftest import skipif_not_all_env_vars_set

pytestmark = skipif_not_all_env_vars_set(["PAGURE_TOKEN", "PAGURE_USER"])


@pytest.fixture()
def pagure_token():
    return os.environ["PAGURE_TOKEN"]


@pytest.fixture()
def pagure_user():
    return os.environ["PAGURE_USER"]


@pytest.fixture()
def pagure_service(pagure_token):
    return PagureService(token=pagure_token)


@pytest.fixture()
def docker_py_project(pagure_service):
    docker_py = pagure_service.get_project(
        namespace="rpms", repo="python-docker", username="lachmanfrantisek"
    )
    return docker_py


@pytest.fixture()
def abiword_project(pagure_service):
    abiword = pagure_service.get_project(
        namespace="rpms", repo="abiword", username="churchyard"
    )
    return abiword


@pytest.fixture()
def abiword_project_fork(pagure_service):
    abiword = pagure_service.get_project(
        namespace="rpms", repo="abiword", username="churchyard", is_fork=True
    )
    return abiword


@pytest.fixture()
def abiword_project_non_existing_fork(pagure_service):
    abiword = pagure_service.get_project(
        namespace="rpms", repo="abiword", username="qwertzuiopasdfghjkl", is_fork=True
    )
    return abiword


def test_pr_comments(abiword_project):
    pr_comments = abiword_project.get_pr_comments(1)
    assert pr_comments
    assert len(pr_comments) == 2
    assert pr_comments[0].comment.startswith("rebased")


def test_pr_comments_reversed(abiword_project):
    pr_comments = abiword_project.get_pr_comments(1, reverse=True)
    assert pr_comments
    assert len(pr_comments) == 2
    assert pr_comments[1].comment.startswith("rebased")


def test_pr_comments_filter(abiword_project):
    pr_comments = abiword_project.get_pr_comments(1, filter_regex="rebased")
    assert pr_comments
    assert len(pr_comments) == 1
    assert pr_comments[0].comment.startswith("rebased")

    pr_comments = abiword_project.get_pr_comments(1, filter_regex="onto ([a-z0-9]*)")
    assert pr_comments
    assert len(pr_comments) == 1
    assert pr_comments[0].comment.startswith("rebased")


def test_pr_comments_search(abiword_project):
    comment_match = abiword_project.search_in_pr(1, filter_regex="rebased")
    assert comment_match
    assert comment_match[0] == "rebased"

    comment_match = abiword_project.search_in_pr(1, filter_regex="onto ([a-z0-9]*)")
    assert comment_match
    assert comment_match[0].startswith("onto")
    assert comment_match[1].startswith("09ac068")


def test_description(docker_py_project):
    description = docker_py_project.get_description()
    assert description == "The python-docker rpms"


def test_branches(docker_py_project):
    branches = docker_py_project.get_branches()
    assert branches
    assert set(branches) == {"f26", "f27", "f28", "f29", "master"}


def test_git_urls(docker_py_project):
    urls = docker_py_project.get_git_urls()
    assert urls
    assert len(urls) == 2
    assert "git" in urls
    assert "ssh" in urls
    assert urls["git"] == "https://src.fedoraproject.org/rpms/python-docker.git"
    assert urls["ssh"].endswith("@pkgs.fedoraproject.org/rpms/python-docker.git")


def test_pr_list(abiword_project):
    pr_list = abiword_project.get_pr_list()
    assert isinstance(pr_list, list)
    assert not pr_list

    pr_list = abiword_project.get_pr_list(status=PRStatus.all)
    assert pr_list
    assert len(pr_list) == 2


def test_pr_info(abiword_project):
    pr_info = abiword_project.get_pr_info(pr_id=1)
    assert pr_info
    assert pr_info.title.startswith("Update Python 2 dependency")
    assert pr_info.status == PRStatus.merged


def test_commit_flags(abiword_project):
    flags = abiword_project.get_commit_flags(
        commit="d87466de81c72231906a6597758f37f28830bb71"
    )
    assert isinstance(flags, list)
    assert len(flags) == 0


def test_fork(abiword_project_fork):
    assert abiword_project_fork.exists()
    fork_description = abiword_project_fork.get_description()
    assert fork_description


def test_nonexisting_fork(abiword_project_non_existing_fork):
    assert not abiword_project_non_existing_fork.exists()
    with pytest.raises(APIError) as ex:
        abiword_project_non_existing_fork.get_description()
    assert "Project not found" in ex.value.args


def test_fork_property(abiword_project):
    fork = abiword_project.get_fork()
    assert fork
    assert fork.get_description()


@pytest.mark.skip
def test_create_fork(docker_py_project):
    not_existing_fork = docker_py_project.get_fork()
    assert not not_existing_fork
    docker_py_project.fork_create()
    assert docker_py_project.get_fork().exists()


def test_username(pagure_service, pagure_user):
    assert pagure_service.user.get_username() == pagure_user


def test_get_file(docker_py_project):
    file_content = docker_py_project.get_file_content(".gitignore")
    assert file_content
    assert isinstance(file_content, str)
    assert "docker-2.6.1.tar.gz" in file_content


def test_nonexisting_file(docker_py_project):
    with pytest.raises(FileNotFoundError) as _:
        docker_py_project.get_file_content(".blablabla_nonexisting_file")

import os

import pytest
from libpagure import APIError

from ogr.abstract import PRStatus
from ogr.services.github import GithubService
from tests.integration.conftest import skipif_not_all_env_vars_set

pytestmark = skipif_not_all_env_vars_set(["GITHUB_TOKEN", "GITHUB_USER"])


@pytest.fixture()
def github_token():
    return os.environ["GITHUB_TOKEN"]


@pytest.fixture()
def github_user():
    return os.environ["GITHUB_USER"]


@pytest.fixture()
def github_service(github_token):
    return GithubService(token=github_token)


@pytest.fixture()
def colin_project(github_service):
    colin_project = github_service.get_project(
        namespace="user-cont", repo="colin", username="lachmanfrantisek"
    )
    return colin_project


@pytest.fixture()
def colin_project_fork(github_service):
    colin_fork = github_service.get_project(
        namespace="user-cont", repo="colin", username="lachmanfrantisek", is_fork=True
    )
    return colin_fork


@pytest.fixture()
def colin_project_non_existing_fork(github_service):
    colin_fork = github_service.get_project(
        namespace="user-cont",
        repo="colin",
        username="askdjalkjdakjsdlkajsd",
        is_fork=True,
    )
    return colin_fork


def test_pr_comments(colin_project):
    pr_comments = colin_project.get_pr_comments(7)
    assert pr_comments
    assert len(pr_comments) == 2
    assert pr_comments[0].comment.endswith("I've just integrated your thoughts.")
    assert pr_comments[1].comment.startswith("Thank you!")


def test_pr_comments_reversed(colin_project):
    pr_comments = colin_project.get_pr_comments(7, reverse=True)
    assert pr_comments
    assert len(pr_comments) == 2
    assert pr_comments[0].comment.startswith("Thank you!")


def test_pr_comments_filter(colin_project):
    pr_comments = colin_project.get_pr_comments(7, filter_regex="Thank")
    assert pr_comments
    assert len(pr_comments) == 2
    assert pr_comments[1].comment.startswith("Thank you!")

    pr_comments = colin_project.get_pr_comments(
        7, filter_regex="Thank you for the ([a-z]*)"
    )
    assert pr_comments
    assert len(pr_comments) == 1
    assert pr_comments[0].comment.endswith("thoughts.")


def test_pr_comments_search(colin_project):
    comment_match = colin_project.search_in_pr(7, filter_regex="Thank")
    assert comment_match
    assert comment_match[0] == "Thank"

    comment_match = colin_project.search_in_pr(
        7, filter_regex="Thank you for the ([a-z]*)"
    )
    assert comment_match
    assert comment_match[0] == "Thank you for the review"
    assert comment_match[1] == "review"


def test_description(colin_project):
    description = colin_project.get_description()
    assert description.startswith("Tool to check generic")


def test_branches(colin_project):
    branches = colin_project.get_branches()
    assert branches
    assert set(branches) == {"master", "overriden-labels-check"}


def test_git_urls(colin_project):
    urls = colin_project.get_git_urls()
    assert urls
    assert len(urls) == 2
    assert "git" in urls
    assert "ssh" in urls
    assert urls["git"] == "https://github.com/user-cont/colin.git"
    assert urls["ssh"].endswith("git@github.com:user-cont/colin.git")


def test_pr_list(colin_project, colin_project_fork):
    pr_list = colin_project_fork.get_pr_list()
    assert isinstance(pr_list, list)
    assert not pr_list

    pr_list_all = colin_project.get_pr_list(status=PRStatus.all)
    assert pr_list_all
    assert len(pr_list_all) >= 144

    pr_list_closed = colin_project.get_pr_list(status=PRStatus.closed)
    assert pr_list_closed
    assert len(pr_list_closed) >= 140

    pr_list = colin_project.get_pr_list()
    assert pr_list
    assert len(pr_list) >= 2


def test_get_releases(colin_project):
    releases = colin_project.get_releases()
    assert releases

    assert len(releases) >= 9


def test_pr_info(colin_project):
    pr_info = colin_project.get_pr_info(pr_id=1)
    assert pr_info
    assert pr_info.title.startswith("Add basic structure")
    assert pr_info.status == PRStatus.closed


def test_commit_flags(colin_project):
    flags = colin_project.get_commit_flags(
        commit="d87466de81c72231906a6597758f37f28830bb71"
    )
    assert isinstance(flags, list)
    assert len(flags) == 0


def test_fork(colin_project_fork):
    assert colin_project_fork.exists()
    fork_description = colin_project_fork.get_description()
    assert fork_description


def test_nonexisting_fork(colin_project_non_existing_fork):
    assert not colin_project_non_existing_fork.exists()
    with pytest.raises(APIError) as ex:
        colin_project_non_existing_fork.get_description()
    assert "Project not found" in ex.value.args


def test_fork_property(colin_project):
    fork = colin_project.get_fork()
    assert fork
    assert fork.get_description()


@pytest.mark.skip
def test_create_fork(colin_project):
    not_existing_fork = colin_project.get_fork()
    assert not not_existing_fork
    colin_project.fork_create()
    assert colin_project.get_fork().exists()


def test_username(github_service, github_user):
    assert github_service.user.get_username() == github_user


def test_get_file(colin_project):
    file_content = colin_project.get_file_content(".gitignore")
    assert file_content
    assert isinstance(file_content, str)
    assert "*.py[co]" in file_content


def test_nonexisting_file(colin_project):
    with pytest.raises(FileNotFoundError) as _:
        colin_project.get_file_content(".blablabla_nonexisting_file")

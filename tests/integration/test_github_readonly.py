import os

import pytest
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
    return GithubService(token=github_token, read_only=True)


@pytest.fixture()
def colin_project(github_service):
    colin_project = github_service.get_project(
        namespace="user-cont", repo="colin", username="lachmanfrantisek"
    )
    return colin_project


def test_pr_comments(colin_project):
    pr_comments = colin_project.get_pr_comments(7)
    assert pr_comments
    assert len(pr_comments) == 2
    assert pr_comments[0].comment.endswith("I've just integrated your thoughts.")
    assert pr_comments[1].comment.startswith("Thank you!")


def test_create_pr(colin_project):
    pr = colin_project.pr_create("title", "text", "master", "souce_branch")
    assert pr.title == "title"


def test_create_fork(colin_project):
    fork = colin_project.fork_create()
    assert not fork.is_fork

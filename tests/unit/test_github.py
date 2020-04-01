import pytest
from flexmock import flexmock

from ogr.services.github.project import GithubProject
from ogr.services.github.pull_request import GithubPullRequest


@pytest.fixture
def github_project(mock_github_repo):
    github_project = GithubProject(
        repo="test_repo", service="test_service", namespace="test_namespace"
    )
    parent_github_project = GithubProject(
        repo="test_parent_repo",
        service="test_service",
        namespace="test_parent_namespace",
    )
    flexmock(github_project)
    flexmock(parent_github_project)
    flexmock(GithubPullRequest)

    github_project.should_receive("github_repo").and_return(mock_github_repo())
    parent_github_project.should_receive("github_repo").and_return(mock_github_repo())
    github_project.should_receive("parent").and_return(parent_github_project)
    return github_project


class TestGithubProject:
    @pytest.mark.parametrize(
        "fork_username",
        [
            pytest.param("test_fork_username", id="fork_username_set"),
            pytest.param(None, id="fork_username_None"),
        ],
    )
    def test_pr_create_is_not_fork(self, github_project, fork_username):
        github_project.should_receive("is_fork").and_return(False)
        GithubPullRequest.should_receive("__init__").and_return()

        head = ":".join(filter(None, [fork_username, "master"]))

        github_project.github_repo.should_call("create_pull").with_args(
            title="test_title", body="test_content", base="master", head=head
        )
        github_project.parent.github_repo.should_call("create_pull").never()
        github_project.github_repo.should_call("create_pull").once()

        github_project.pr_create(
            title="test_title",
            body="test_content",
            target_branch="master",
            source_branch="master",
            fork_username=fork_username,
        )

    @pytest.mark.parametrize(
        "fork_username",
        [
            pytest.param("test_fork_username", id="fork_username_set"),
            pytest.param(None, id="fork_username_None"),
        ],
    )
    def test_pr_create_is_fork(self, github_project, fork_username):
        github_project.should_receive("is_fork").and_return(True)
        GithubPullRequest.should_receive("__init__").and_return()

        github_project.parent.github_repo.should_call("create_pull").with_args(
            title="test_title",
            body="test_content",
            base="master",
            head=f"{github_project}:master",
        )
        github_project.parent.github_repo.should_call("create_pull").once()
        github_project.github_repo.should_call("create_pull").never()

        github_project.pr_create(
            title="test_title",
            body="test_content",
            target_branch="master",
            source_branch="master",
            fork_username=fork_username,
        )

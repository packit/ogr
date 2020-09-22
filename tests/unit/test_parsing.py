import pytest

from ogr.parsing import parse_git_repo, RepoUrl


@pytest.mark.parametrize(
    "url,result",
    [
        (
            "https://host.name/namespace/repo",
            RepoUrl(
                repo="repo", namespace="namespace", scheme="https", hostname="host.name"
            ),
        ),
        (
            "https://host.name/namespace/repo.git",
            RepoUrl(
                repo="repo", namespace="namespace", scheme="https", hostname="host.name"
            ),
        ),
        (
            "http://host.name/namespace/repo",
            RepoUrl(
                repo="repo", namespace="namespace", scheme="http", hostname="host.name"
            ),
        ),
        (
            "git://host.name/namespace/repo",
            RepoUrl(
                repo="repo", namespace="namespace", scheme="git", hostname="host.name"
            ),
        ),
        (
            "git+https://host.name/namespace/repo",
            RepoUrl(
                repo="repo",
                namespace="namespace",
                scheme="git+https",
                hostname="host.name",
            ),
        ),
        (
            "git@host.name:namespace/repo",
            RepoUrl(
                repo="repo",
                namespace="namespace",
                scheme="http",
                hostname="host.name",
                username="namespace",
            ),
        ),
        ("host.name/repo", RepoUrl(repo="repo", scheme="http", hostname="host.name")),
        (
            "host.name/fork/user/namespace/repo",
            RepoUrl(
                repo="repo",
                username="user",
                namespace="namespace",
                scheme="http",
                hostname="host.name",
                is_fork=True,
            ),
        ),
        (
            "https://host.name/namespace/repo/",
            RepoUrl(
                repo="repo",
                username=None,
                namespace="namespace",
                scheme="https",
                hostname="host.name",
            ),
        ),
        (
            "https://host.name/multi/part/namespace/repo/",
            RepoUrl(
                repo="repo",
                username=None,
                namespace="multi/part/namespace",
                scheme="https",
                hostname="host.name",
            ),
        ),
        (
            "https://pagure.io/fork/user/some_repo",
            RepoUrl(
                repo="some_repo",
                username="user",
                namespace="",
                is_fork=True,
                hostname="pagure.io",
                scheme="https",
            ),
        ),
        ("https://fail@more@at@domain.com", None),
    ],
)
def test_parse_git_repo(url, result):
    repo_url = parse_git_repo(potential_url=url)
    assert repo_url == result

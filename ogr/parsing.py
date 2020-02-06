# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Optional
from urllib.parse import urlparse


class RepoUrl:
    def __init__(
        self,
        repo: str,
        namespace: Optional[str] = None,
        username: Optional[str] = None,
        is_fork: bool = False,
        hostname: Optional[str] = None,
        scheme: Optional[str] = None,
    ) -> None:
        self.repo = repo
        self.namespace = namespace
        self.username = username
        self.is_fork = is_fork
        self.hostname = hostname
        self.scheme = scheme

    def get_instance_url(self) -> str:
        scheme = self.scheme or "http"
        return f"{scheme}://{self.hostname}"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, RepoUrl):
            return False

        return (
            self.repo == o.repo
            and self.namespace == o.namespace
            and self.username == o.username
            and self.is_fork == o.is_fork
            and self.hostname == o.hostname
            and self.scheme == o.scheme
        )

    def __str__(self) -> str:
        repo_url_str = (
            f"RepoUrl(repo='{self.repo}', "
            f"namespace='{self.namespace}', "
            f"is_fork={self.is_fork}, "
            f"hostname='{self.hostname}', "
            f"scheme='{self.scheme}'"
        )
        if self.username:
            repo_url_str += f", username='{self.username}'"
        repo_url_str += ")"
        return repo_url_str


def parse_git_repo(potential_url: str) -> Optional[RepoUrl]:
    """Cover the following variety of URL forms for Github/Gitlab repo referencing.

    1) www.domain.com/foo/bar
    2) (same as above, but with ".git" in the end)
    3) (same as the two above, but without "www.")
    # all of the three above, but starting with "http://", "https://", "git://", "git+https://"
    4) git@domain.com:foo/bar
    5) (same as above, but with ".git" in the end)
    6) (same as the two above but with "ssh://" in front or with "git+ssh" instead of "git")
    7) pagure format of forks (e.g. domain.com/fork/username/namespace/project

    Notably, the repo *must* have exactly username and reponame, nothing else and nothing
    more. E.g. `github.com/<username>/<reponame>/<something>` is *not* recognized.
    """
    if not potential_url:
        return None

    # Remove trailing '/' from 1-7 to ensure parsing works as expected.
    if potential_url[-1] == "/":
        potential_url = potential_url.rstrip("/")

    # transform 4-6 to a URL-like string, so that we can handle it together with 1-3
    if "@" in potential_url:
        split = potential_url.split("@")
        if len(split) == 2:
            potential_url = "http://" + split[1]
        else:
            # more @s ?
            return None

    # make it parsable by urlparse if it doesn't contain scheme
    if not potential_url.startswith(("http://", "https://", "git://", "git+https://")):
        potential_url = "http://" + potential_url

    # urlparse should handle it now
    parsed = urlparse(potential_url)

    username = None
    if ":" in parsed.netloc:
        # e.g. domain.com:foo or domain.com:1234, where foo is username, but 1234 is port number
        split = parsed.netloc.split(":")
        if split[1] and not split[1].isnumeric():
            username = split[1]

    # path starts with '/', strip it away
    path = parsed.path.lstrip("/")

    # strip trailing '.git'
    if path.endswith(".git"):
        path = path[: -len(".git")]

    split = path.split("/")
    if len(split) == 1:
        # path contains only reponame
        return RepoUrl(
            namespace=username,
            repo=path,
            username=username,
            hostname=parsed.hostname,
            scheme=parsed.scheme,
        )
    if not username and len(split) >= 2:
        # path contains username/reponame

        is_fork = "fork" in split
        if is_fork and len(split) == 4:
            username = split[1]

        return RepoUrl(
            namespace=split[-2],
            repo=split[-1],
            username=username,
            is_fork=is_fork,
            hostname=parsed.hostname,
            scheme=parsed.scheme,
        )

    # all other cases
    return None


def get_username_from_git_url(url: str) -> Optional[str]:
    """http://github.com/foo/bar.git -> foo"""
    repo_url = parse_git_repo(url)
    if repo_url:
        return repo_url.username
    return None


def get_reponame_from_git_url(url: str) -> Optional[str]:
    """http://github.com/foo/bar.git -> bar"""
    repo_url = parse_git_repo(url)
    if repo_url:
        return repo_url.repo
    return None


def strip_dot_git(url: str) -> str:
    """Strip trailing .git"""
    return url[: -len(".git")] if url.endswith(".git") else url

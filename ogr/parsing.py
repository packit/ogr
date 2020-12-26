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

from typing import Optional, Tuple, List
from urllib.parse import urlparse, ParseResult


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

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def _prepare_url(potential_url: str) -> Optional[ParseResult]:
        # Remove trailing '/' to ensure parsing works as expected.
        potential_url = potential_url.rstrip("/")

        # transform SSH URL
        if "@" in potential_url:
            split = potential_url.split("@")
            if len(split) == 2:
                potential_url = "https://" + split[1]
            else:
                # more @s ?
                return None

        # make it parsable by urlparse if it doesn't contain scheme
        if not potential_url.startswith(
            ("http://", "https://", "git://", "git+https://")
        ):
            potential_url = "https://" + potential_url

        return urlparse(potential_url)

    def _set_hostname_and_scheme(self, parsed_url: ParseResult):
        self.hostname = parsed_url.hostname
        self.scheme = parsed_url.scheme

    def _parse_username(self, parsed: ParseResult) -> bool:
        if ":" not in parsed.netloc:
            return True

        split = parsed.netloc.split(":")
        if len(split) > 2:
            # in case there is port:namespace
            return False

        if not split[1]:
            return True

        if split[1] == "forks":
            self.is_fork = True
        elif not split[1].isnumeric():
            # e.g. domain.com:foo or domain.com:1234,
            # where foo is username, but 1234 is port number
            self.username = split[1]

        return True

    @staticmethod
    def _prepare_path(parsed: ParseResult) -> Tuple[str, List[str]]:
        # path starts with '/', strip it away
        path = parsed.path.lstrip("/")

        # strip trailing '.git'
        if path.endswith(".git"):
            path = path[:-4]

        return path, path.split("/")

    def _check_fork(self, splits: List[str]) -> List[str]:
        if self.is_fork:
            # we got pagure fork but SSH url
            self.username = splits[0]
            return splits[1:-1]

        # path contains username/reponame
        # or some/namespace/reponame
        # or fork/username/some/namespace/reponame
        self.is_fork = (
            splits[0] in ("fork", "forks") and len(splits) >= 3
        )  # pagure fork
        if self.is_fork:
            # fork/username/namespace/repo format
            self.username = splits[1]
            return splits[2:-1]

        if self.username:
            return [self.username] + splits[:-1]

        self.username = splits[0]
        return splits[:-1]

    def _parsed_path(self, path: str, splits: List[str]) -> Optional["RepoUrl"]:
        if len(splits) == 1:
            self.namespace = self.username
            self.repo = path

            return self

        if len(splits) < 2:
            # invalid cases
            return None

        namespace_parts = self._check_fork(splits)

        self.namespace = "/".join(namespace_parts)
        self.repo = splits[-1]

        return self

    @classmethod
    def parse(cls, potential_url: str) -> Optional["RepoUrl"]:
        if not potential_url:
            return None

        repo = RepoUrl(None)
        parsed_url = cls._prepare_url(potential_url)
        if not parsed_url:
            return None

        repo._set_hostname_and_scheme(parsed_url)
        if not repo._parse_username(parsed_url):
            # failed parsing username
            return None

        return repo if repo._parsed_path(*cls._prepare_path(parsed_url)) else None


def parse_git_repo(potential_url: str) -> Optional[RepoUrl]:
    """Cover the following variety of URL forms for Github/Gitlab repo referencing.

    1) www.domain.com/foo/bar
    2) (same as above, but with ".git" in the end)
    3) (same as the two above, but without "www.")
    # all of the three above, but starting with "http://", "https://", "git://", "git+https://"
    4) git@domain.com:foo/bar
    5) (same as above, but with ".git" in the end)
    6) (same as the two above but with "ssh://" in front or with "git+ssh" instead of "git")
    7) pagure format of forks (e.g. domain.com/fork/username/namespace/project)
    8) nested groups on GitLab or Pagure (empty namespace is supported as well)
    """
    return RepoUrl.parse(potential_url)


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

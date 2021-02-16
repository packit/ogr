# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Optional, Tuple, List
from urllib.parse import urlparse, ParseResult


class RepoUrl:
    """
    Class that represents repo URL.

    Attributes:
        repo (str): Name of the repository.
        namespace (Optional[str]): Namespace of the repository, if has any.
        username (Optional[str]): Username of the repository owner, if can be
            specified.
        is_fork (bool): Flag denoting if repository is a fork, if can be
            specified (Pagure).
        hostname (Optional[str]): Hostname of host of the repository.
        scheme (Optional[str]): Protocol used to access repository.
    """

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
        """
        Returns:
            Instance URL of host of the repository.
        """
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
        """
        Details in `parse_git_repo` function.

        Args:
            potential_url: URL of a git repository.

        Returns:
            RepoUrl instance if can be parsed, `None` otherwise.
        """
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
    """
    Parses given URL of a git repository.

    ### Covered scenarios

    1. URL in form: `www.domain.com/foo/bar`
        - with trailing `.git`
        - without `www.`
        - starting with `http://`, `https://`, `git://` or `git+https://`
    2. URL in form: `git@domain.com:foo/bar`
        - with trailing `.git`
        - with `ssh://` at the start or with `git+ssh` instead of `git`
    8. Pagure format of forks, e.g.
       `domain.com/fork/username/namespace/project`
    9. Nested groups on GitLab or Pagure (empty namespace is supported as well)

    Args:
        potential_url: URL of a git repository.

    Returns:
        Object of RepoUrl class if can be parsed, `None` otherwise.
    """
    return RepoUrl.parse(potential_url)


def get_username_from_git_url(url: str) -> Optional[str]:
    """
    Returns username from the git URL.

    Args:
        url: URL of the git repository.

    Returns:
        Username if can be parsed, `None` otherwise.
    """
    repo_url = parse_git_repo(url)
    if repo_url:
        return repo_url.username
    return None


def get_reponame_from_git_url(url: str) -> Optional[str]:
    """
    Returns repository name from the git URL.

    Args:
        url: URL of the git repository.

    Returns:
        Repository name if can be parsed, `None` otherwise.
    """
    repo_url = parse_git_repo(url)
    if repo_url:
        return repo_url.repo
    return None


def strip_dot_git(url: str) -> str:
    """
    Strips `.git` from the given URL of a git repository.

    Args:
        url: URL of the git repository.

    Returns:
        URL without trailing `.git`.
    """
    """Strip trailing .git"""
    return url[: -len(".git")] if url.endswith(".git") else url

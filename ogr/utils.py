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

import logging
import os
import re
import subprocess
from typing import List, Union, Match, Optional, Dict, Tuple, Any
import git

from ogr.abstract import AnyComment, Comment

logger = logging.getLogger(__name__)


def clone_repo_and_cd_inside(repo_name: str, repo_ssh_url: str, namespace: str) -> None:

    logger.debug("clone %s", repo_ssh_url)
    try:
        git.Repo.clone_from(repo_ssh_url, namespace)
    except git.exc.GitCommandError:
        logger.error("Clone failed")

    os.chdir(namespace)


def set_upstream_remote(clone_url: str, ssh_url: str, pull_merge_name: str) -> None:
    logger.debug("set remote upstream to %s", clone_url)
    repo = git.Repo()

    try:
        repo.create_remote("upstream", url=clone_url)
    except git.exc.GitCommandError:
        for remote in repo.remotes:
            if remote.name == "upstream":
                remote.set_url(clone_url)
                break

    try:
        repo.create_remote("upstream-w", url=ssh_url)
    except git.exc.GitCommandError:
        for remote in repo.remotes:
            if remote.name == "upstream-w":
                remote.set_url(ssh_url)
                break

    subprocess.run(
        [
            "git",
            "config",
            "--local",
            "--add",
            "remote.upstream.fetch",
            "+refs/{}/*/head:refs/remotes/upstream/{}r/*".format(
                pull_merge_name, pull_merge_name[0]
            ),
        ],
        check=True,
    )


def set_origin_remote(ssh_url: str, pull_merge_name: str) -> None:
    logger.debug("set remote origin to %s", ssh_url)

    remotes = git.Repo().remotes

    for remote in remotes:
        if remote.name == "origin":
            remote.set_url(ssh_url)
            break

    logger.debug("adding fetch rule to get PRs for origin")
    subprocess.run(
        [
            "git",
            "config",
            "--local",
            "--add",
            "remote.origin.fetch",
            "+refs/{}/*/head:refs/remotes/origin/{}r/*".format(
                pull_merge_name, pull_merge_name[0]
            ),
        ],
        check=True,
    )


def fetch_all() -> None:
    logger.debug("fetching everything")

    remotes = git.Repo().remotes
    for remote in remotes:
        remote.fetch()


def filter_comments(
    comments: List[AnyComment],
    filter_regex: Optional[str] = None,
    reverse: bool = False,
    author: Optional[str] = None,
) -> List[AnyComment]:
    if reverse:
        comments.reverse()

    if filter_regex or author:
        pattern = None
        if filter_regex:
            pattern = re.compile(filter_regex)

        comments = list(
            filter(
                lambda comment: (not pattern or bool(pattern.search(comment.body)))
                and (not author or comment.author == author),
                comments,
            )
        )
    return comments


def search_in_comments(
    comments: List[Union[str, Comment]], filter_regex: str
) -> Optional[Match[str]]:
    """
    Find match in pull-request description or comments.

    :param comments: [str or PRComment]
    :param filter_regex: filter the comments' content with re.search
    :return: re.Match or None
    """
    pattern = re.compile(filter_regex)
    for comment in comments:
        if isinstance(comment, Comment):
            comment = comment.body
        re_search = pattern.search(comment)
        if re_search:
            return re_search
    return None


class RequestResponse:
    def __init__(
        self,
        status_code: int,
        ok: bool,
        content: bytes,
        json: Optional[Dict[Any, Any]] = None,
        reason: Optional[str] = None,
        headers: Optional[List[Tuple[Any, Any]]] = None,
        links: Optional[List[str]] = None,
        exception: Optional[Dict[Any, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.ok = ok
        self.content = content
        self.json_content = json
        self.reason = reason
        self.headers = dict(headers) if headers else None
        self.links = links
        self.exception = exception

    def __str__(self) -> str:
        return (
            f"RequestResponse("
            f"status_code={self.status_code}, "
            f"ok={self.ok}, "
            f"content={self.content.decode()}, "
            f"json={self.json_content}, "
            f"reason={self.reason}, "
            f"headers={self.headers}, "
            f"links={self.links}, "
            f"exception={self.exception})"
        )

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, RequestResponse):
            return False
        return (
            self.status_code == o.status_code
            and self.ok == o.ok
            and self.content == o.content
            and self.json_content == o.json_content
            and self.reason == o.reason
            and self.headers == o.headers
            and self.links == o.links
            and self.exception == o.exception
        )

    def to_json_format(self) -> Dict[str, Any]:
        output = {
            "status_code": self.status_code,
            "ok": self.ok,
            "content": self.content,
        }
        if self.json_content:
            output["json"] = self.json_content
        if self.reason:
            output["reason"] = self.reason
        if self.headers:
            output["headers"] = self.headers
        if self.links:
            output["links"] = self.links
        if self.exception:
            output["exception"] = self.exception
        return output

    def json(self) -> Optional[Dict[Any, Any]]:
        return self.json_content


def filter_paths(paths: List[str], filter_regex: str) -> List[str]:
    """
    Find match in paths.
    :param paths:
    :param filter_regex:
    :return: [str]
    """
    pattern = re.compile(filter_regex)
    paths = list(
        filter(lambda path: (not pattern or bool(pattern.search(path))), paths)
    )
    return paths

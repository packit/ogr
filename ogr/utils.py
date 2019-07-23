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
from typing import List, Union, Match, Optional

import six

from ogr.abstract import PRComment
from ogr.constant import CLONE_TIMEOUT

logger = logging.getLogger(__name__)


def clone_repo_and_cd_inside(repo_name, repo_ssh_url, namespace):
    os.makedirs(namespace, exist_ok=True)
    os.chdir(namespace)
    logger.debug("clone %s", repo_ssh_url)

    proc = subprocess.run(
        ["git", "clone", repo_ssh_url], stderr=subprocess.PIPE, timeout=CLONE_TIMEOUT
    )
    output = proc.stderr.decode()
    logger.debug("Clone exited with {} and output: {}".format(proc.returncode, output))
    if "does not exist" in output:
        logger.error("Clone failed.")
        raise Exception("Clone failed")

    # if the repo is already cloned, it's not an issue
    os.chdir(repo_name)


def set_upstream_remote(clone_url, ssh_url, pull_merge_name):
    logger.debug("set remote upstream to %s", clone_url)
    try:
        subprocess.run(["git", "remote", "add", "upstream", clone_url], check=True)
    except subprocess.CalledProcessError:
        subprocess.run(["git", "remote", "set-url", "upstream", clone_url], check=True)
    try:
        subprocess.run(["git", "remote", "add", "upstream-w", ssh_url], check=True)
    except subprocess.CalledProcessError:
        subprocess.run(["git", "remote", "set-url", "upstream-w", ssh_url], check=True)
    logger.debug("adding fetch rule to get PRs for upstream")
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


def set_origin_remote(ssh_url, pull_merge_name):
    logger.debug("set remote origin to %s", ssh_url)
    subprocess.run(["git", "remote", "set-url", "origin", ssh_url], check=True)
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


def fetch_all():
    logger.debug("fetching everything")
    with open("/dev/null", "w") as fd:
        subprocess.run(["git", "fetch", "--all"], stdout=fd, check=True)


def filter_comments(comments: List[PRComment], filter_regex: str) -> List[PRComment]:
    pattern = re.compile(filter_regex)
    comments = list(
        filter(lambda comment: bool(pattern.search(comment.comment)), comments)
    )
    return comments


def search_in_comments(
    comments: List[Union[str, PRComment]], filter_regex: str
) -> Optional[Match[str]]:
    """
    Find match in pull-request description or comments.

    :param comments: [str or PRComment]
    :param filter_regex: filter the comments' content with re.search
    :return: re.Match or None
    """
    pattern = re.compile(filter_regex)
    for comment in comments:
        if not isinstance(comment, six.string_types):
            comment = comment.comment
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
        json: Optional[dict] = None,
        reason=None,
    ) -> None:
        self.status_code = status_code
        self.ok = ok
        self.content = content
        self.json = json
        self.reason = reason

    def __str__(self) -> str:
        return (
            f"RequestResponse("
            f"status_code={self.status_code}, "
            f"ok={self.ok}, "
            f"content={self.content}, "
            f"json={self.json}, "
            f"reason={self.reason})"
        )

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, RequestResponse):
            return False
        return (
            self.status_code == o.status_code
            and self.ok == o.ok
            and self.content == o.content
            and self.json == o.json
            and self.reason == o.reason
        )

    def to_json_format(self) -> dict:
        return {
            "status_code": self.status_code,
            "ok": self.ok,
            "content": self.content,
            "json": self.json,
            "reason": self.reason,
        }


class SingletonMeta(type):
    _instance = None

    def __call__(self):
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance

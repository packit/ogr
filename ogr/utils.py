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

import datetime
import logging
import os
import re
import subprocess
import tempfile
from time import sleep
from typing import List, Union, Match, Optional

import six

from ogr.abstract import PRComment
from ogr.constant import CLONE_TIMEOUT

logger = logging.getLogger(__name__)


def clone_repo_and_cd_inside(repo_name, repo_ssh_url, namespace):
    os.makedirs(namespace, exist_ok=True)
    os.chdir(namespace)
    logger.debug("clone %s", repo_ssh_url)

    for _ in range(CLONE_TIMEOUT):
        proc = subprocess.Popen(["git", "clone", repo_ssh_url], stderr=subprocess.PIPE)
        output = proc.stderr.read().decode()
        logger.debug(
            "Clone exited with {} and output: {}".format(proc.returncode, output)
        )
        if "does not exist yet" not in output:
            break
        sleep(1)
    else:
        logger.error("Clone failed.")
        raise Exception("Clone failed")

    # if the repo is already cloned, it's not an issue
    os.chdir(repo_name)


def set_upstream_remote(clone_url, ssh_url, pull_merge_name):
    logger.debug("set remote upstream to %s", clone_url)
    try:
        subprocess.check_call(["git", "remote", "add", "upstream", clone_url])
    except subprocess.CalledProcessError:
        subprocess.check_call(["git", "remote", "set-url", "upstream", clone_url])
    try:
        subprocess.check_call(["git", "remote", "add", "upstream-w", ssh_url])
    except subprocess.CalledProcessError:
        subprocess.check_call(["git", "remote", "set-url", "upstream-w", ssh_url])
    logger.debug("adding fetch rule to get PRs for upstream")
    subprocess.check_call(
        [
            "git",
            "config",
            "--local",
            "--add",
            "remote.upstream.fetch",
            "+refs/{}/*/head:refs/remotes/upstream/{}r/*".format(
                pull_merge_name, pull_merge_name[0]
            ),
        ]
    )


def set_origin_remote(ssh_url, pull_merge_name):
    logger.debug("set remote origin to %s", ssh_url)
    subprocess.check_call(["git", "remote", "set-url", "origin", ssh_url])
    logger.debug("adding fetch rule to get PRs for origin")
    subprocess.check_call(
        [
            "git",
            "config",
            "--local",
            "--add",
            "remote.origin.fetch",
            "+refs/{}/*/head:refs/remotes/origin/{}r/*".format(
                pull_merge_name, pull_merge_name[0]
            ),
        ]
    )


def fetch_all():
    logger.debug("fetching everything")
    with open("/dev/null", "w") as fd:
        subprocess.check_call(["git", "fetch", "--all"], stdout=fd)


def get_remote_url(remote):
    logger.debug("get remote URL for remote %s", remote)
    try:
        url = subprocess.check_output(["git", "remote", "get-url", remote])
    except subprocess.CalledProcessError:
        remote = "origin"
        logger.warning("falling back to %s", remote)
        url = subprocess.check_output(["git", "remote", "get-url", remote])
    return remote, url.decode("utf-8").strip()


def prompt_for_pr_content(commit_msgs):
    t = tempfile.NamedTemporaryFile(delete=False, prefix="gh.")
    try:
        template = "Title of this PR\n\n{}\n\n".format(commit_msgs)
        template_b = template.encode("utf-8")
        t.write(template_b)
        t.flush()
        t.close()
        try:
            editor_cmdstring = os.environ["EDITOR"]
        except KeyError:
            logger.warning("EDITOR environment variable is not set")
            editor_cmdstring = "/bin/vi"

        logger.debug("using editor: %s", editor_cmdstring)

        cmd = [editor_cmdstring, t.name]

        logger.debug("invoking editor: %s", cmd)
        proc = subprocess.Popen(cmd)
        ret = proc.wait()
        logger.debug("editor returned : %s", ret)
        if ret:
            raise RuntimeError("error from editor")
        with open(t.name) as fd:
            pr_content = fd.read()
        if template == pr_content:
            logger.error("PR description is unchanged")
            raise RuntimeError("The template is not changed, the PR won't be created.")
    finally:
        os.unlink(t.name)
    logger.debug("got: %s", pr_content)
    title, body = pr_content.split("\n", 1)
    logger.debug("title: %s", title)
    logger.debug("body: %s", body)
    return title, body.strip()


def list_local_branches():
    """ return a list of dicts """
    fmt = (
        "%(refname:short);%(upstream:short);%(authordate:iso-strict);%(upstream:track)"
    )
    for_each_ref = (
        subprocess.check_output(["git", "for-each-ref", "--format", fmt, "refs/heads/"])
        .decode("utf-8")
        .strip()
        .split("\n")
    )
    response = []
    was_merged = (
        subprocess.check_output(
            ["git", "branch", "--merged", "master", "--format", "%(refname:short)"]
        )
        .decode("utf-8")
        .strip()
        .split("\n")
    )
    for li in for_each_ref:
        fields = li.split(";")
        response.append(
            {
                "name": fields[0],
                "remote_tracking": fields[1],
                "date": datetime.datetime.strptime(fields[2][:-6], "%Y-%m-%dT%H:%M:%S"),
                "tracking_status": fields[3],
                "merged": "merged" if fields[0] in was_merged else "",
            }
        )
    return response


def get_current_branch_name():
    return (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .decode("utf-8")
        .strip()
    )


def get_commit_msgs(branch):
    return (
        subprocess.check_output(
            ["git", "log", "--pretty=format:- %s.", "%s..HEAD" % branch]
        )
        .decode("utf-8")
        .strip()
    )


def git_push():
    """ perform `git push` """
    # it would make sense to do `git push -u`
    # this command NEEDS to be configurable
    subprocess.check_call(["git", "push", "-q"])


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

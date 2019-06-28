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

from typing import List, Optional, Match, Any

from ogr.abstract import GitService, GitProject, PRComment, GitUser
from ogr.utils import search_in_comments, filter_comments
from ogr.parsing import parse_git_repo


class BaseGitService(GitService):
    def get_project_from_url(self, url: str) -> "GitProject":
        repo_url = parse_git_repo(potential_url=url)
        project = self.get_project(repo=repo_url.repo, namespace=repo_url.namespace)
        return project


class BaseGitProject(GitProject):
    @property
    def full_repo_name(self) -> str:
        """
        Get repo name with namespace
        e.g. 'rpms/python-docker-py'

        :return: str
        """
        return f"{self.namespace}/{self.repo}"

    def get_pr_comments(
        self, pr_id, filter_regex: str = None, reverse: bool = False
    ) -> List[PRComment]:
        """
        Get list of pull-request comments.

        :param pr_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :return: [PRComment]
        """
        all_comments = self._get_all_pr_comments(pr_id=pr_id)
        if reverse:
            all_comments.reverse()
        if filter_regex:
            all_comments = filter_comments(all_comments, filter_regex)
        return all_comments

    def search_in_pr(
        self,
        pr_id: int,
        filter_regex: str,
        reverse: bool = False,
        description: bool = True,
    ) -> Optional[Match[str]]:
        """
        Find match in pull-request description or comments.

        :param description: bool (search in description?)
        :param pr_id: int
        :param filter_regex: filter the comments' content with re.search
        :param reverse: reverse order of comments
        :return: re.Match or None
        """
        all_comments: List[Any] = self.get_pr_comments(pr_id=pr_id, reverse=reverse)
        if description:
            description_content = self.get_pr_info(pr_id).description
            if reverse:
                all_comments.append(description_content)
            else:
                all_comments.insert(0, description_content)

        return search_in_comments(comments=all_comments, filter_regex=filter_regex)


class BaseGitUser(GitUser):
    pass

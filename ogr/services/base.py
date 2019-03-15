from typing import List, Optional, Match, Any

from ogr.abstract import GitService, GitProject, PRComment, GitUser
from ogr.utils import search_in_comments, filter_comments


class BaseGitService(GitService):
    pass


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

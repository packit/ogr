from requre.online_replacing import record_requests_for_all_methods

from tests.integration.pagure.base import PagureTests


@record_requests_for_all_methods()
class Comments(PagureTests):
    def test_pr_comments(self):
        pr_comments = self.ogr_project.get_pr(4).get_comments()
        assert pr_comments
        print(pr_comments[0].body, pr_comments[1].body, pr_comments[2].body)
        assert len(pr_comments) == 8
        assert pr_comments[0].body.endswith("test")

    def test_pr_comments_reversed(self):
        pr_comments = self.ogr_project.get_pr(4).get_comments(reverse=True)
        assert pr_comments
        assert len(pr_comments) == 8
        assert pr_comments[2].body.endswith("PR comment 10")

    def test_pr_comments_filter(self):
        pr_comments = self.ogr_project.get_pr(4).get_comments(filter_regex="me")
        assert pr_comments
        assert len(pr_comments) == 4
        assert pr_comments[0].body == "ignored comment"

        pr_comments = self.ogr_project.get_pr(4).get_comments(
            filter_regex="PR comment [0-9]*"
        )
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[0].body.endswith("aaaa")

    def test_pr_comments_search(self):
        comment_match = self.ogr_project.get_pr(4).search(filter_regex="New")
        assert comment_match
        print(comment_match)
        assert comment_match[0] == "New"

        comment_match = self.ogr_project.get_pr(4).search(
            filter_regex="Pull-Request has been merged by [a-z]*"
        )
        print(comment_match)
        assert comment_match
        assert comment_match[0].startswith("Pull")

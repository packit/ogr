from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base import GithubTests


@record_requests_for_all_methods()
class Comments(GithubTests):
    def test_pr_comments(self):
        pr_comments = self.ogr_project.get_pr(9).get_comments()
        assert pr_comments
        assert len(pr_comments) == 2

        assert pr_comments[0].body.endswith("fixed")
        assert pr_comments[1].body.startswith("LGTM")

    def test_pr_comments_reversed(self):
        pr_comments = self.ogr_project.get_pr(9).get_comments(reverse=True)
        assert pr_comments
        assert len(pr_comments) == 2
        assert pr_comments[0].body.startswith("LGTM")

    def test_pr_comments_filter(self):
        pr_comments = self.ogr_project.get_pr(9).get_comments(filter_regex="fixed")
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].body.startswith("@TomasTomecek")

        pr_comments = self.ogr_project.get_pr(9).get_comments(
            filter_regex="LGTM, nicely ([a-z]*)"
        )
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].body.endswith("done!")

    def test_pr_comments_search(self):
        comment_match = self.ogr_project.get_pr(9).search(filter_regex="LGTM")
        assert comment_match
        assert comment_match[0] == "LGTM"

        comment_match = self.ogr_project.get_pr(9).search(
            filter_regex="LGTM, nicely ([a-z]*)"
        )
        assert comment_match
        assert comment_match[0] == "LGTM, nicely done"

    def test_issue_comments(self):
        comments = self.ogr_project.get_issue(194).get_comments()
        assert len(comments) == 6
        assert comments[0].body.startswith("/packit")

    def test_issue_comments_reversed(self):
        comments = self.ogr_project.get_issue(194).get_comments(reverse=True)
        assert len(comments) == 6
        assert comments[0].body.startswith("The ")

    def test_issue_comments_regex(self):
        comments = self.ogr_project.get_issue(194).get_comments(
            filter_regex=r".*Fedora package.*"
        )
        assert len(comments) == 3
        assert "master" in comments[0].body

    def test_issue_comments_regex_reversed(self):
        comments = self.ogr_project.get_issue(194).get_comments(
            reverse=True, filter_regex=".*Fedora package.*"
        )
        assert len(comments) == 3
        assert "f29" in comments[0].body

    def test_pr_comments_author_regex(self):
        comments = self.ogr_project.get_pr(217).get_comments(
            filter_regex="^I", author="mfocko"
        )
        assert len(comments) == 1
        assert "API" in comments[0].body

    def test_pr_comments_author(self):
        comments = self.ogr_project.get_pr(217).get_comments(author="lachmanfrantisek")
        assert len(comments) == 3
        assert comments[0].body.endswith("here.")

    def test_issue_comments_author_regex(self):
        comments = self.ogr_project.get_issue(220).get_comments(
            filter_regex=".*API.*", author="lachmanfrantisek"
        )
        assert len(comments) == 1
        assert comments[0].body.startswith("After")

    def test_issue_comments_author(self):
        comments = self.ogr_project.get_issue(220).get_comments(author="mfocko")
        assert len(comments) == 2
        assert comments[0].body.startswith("What")
        assert comments[1].body.startswith("Consider")

    def test_issue_comments_updates(self):
        comments = self.hello_world_project.get_issue(61).get_comments(
            filter_regex="comment-update"
        )
        assert len(comments) == 1
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "see if updating works"
        assert comments[0].body == "see if updating works"
        assert comments[0].edited > before_edited

        comments[0].body = before_comment
        assert comments[0].body == before_comment

    def test_pr_comments_updates(self):
        comments = self.hello_world_project.get_pr(72).get_comments(
            filter_regex="comment updates"
        )
        assert len(comments) == 1
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "see if updating works"
        assert comments[0].body == "see if updating works"
        assert comments[0].edited > before_edited

        comments[0].body = before_comment
        assert comments[0].body == before_comment

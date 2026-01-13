# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


from requre.helpers import record_httpx
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.forgejo.base import ForgejoTests


@record_httpx()
@record_requests_for_all_methods()
class Comments(ForgejoTests):
    def test_pr_comments(self):
        pr_comments = list(self.project.get_pr(209).get_comments())
        assert pr_comments
        assert len(pr_comments) == 3

        assert pr_comments[0].body.startswith("LGTM")
        assert pr_comments[1].body.startswith("second comment")

    def test_pr_comments_reversed(self):
        pr_comments = list(self.project.get_pr(209).get_comments(reverse=True))
        assert pr_comments
        assert len(pr_comments) == 3

        assert pr_comments[0].body.startswith("LGTM, nicely done")

    def test_pr_comments_filter(self):
        pr_comments = list(
            self.project.get_pr(209).get_comments(filter_regex="comment"),
        )
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].body.startswith("second")

        pr_comments = list(
            self.project.get_pr(209).get_comments(
                filter_regex="nicely ([a-z]*)",
            ),
        )
        assert pr_comments
        assert len(pr_comments) == 1
        assert pr_comments[0].body.endswith("done")

    def test_pr_comments_search(self):
        comment_match = self.project.get_pr(209).search(filter_regex="LGTM")
        assert comment_match
        assert comment_match[0] == "LGTM"

        comment_match = self.project.get_pr(209).search(
            filter_regex="LGTM, nicely ([a-z]*)",
        )
        assert comment_match
        assert comment_match[0] == "LGTM, nicely done"

    def test_issue_comments(self):
        comments = list(self.project.get_issue(244).get_comments())
        assert len(comments) == 3
        assert comments[0].body.startswith("/packit")

    def test_issue_comments_reversed(self):
        comments = list(self.project.get_issue(244).get_comments(reverse=True))
        assert len(comments) == 3
        assert comments[0].body.startswith("This ")

    def test_issue_comments_regex(self):
        comments = list(
            self.project.get_issue(244).get_comments(
                filter_regex=".*random *",
            ),
        )
        assert len(comments) == 2
        assert "other" in comments[0].body

    def test_issue_comments_regex_reversed(self):
        comments = list(
            self.project.get_issue(244).get_comments(
                reverse=True,
                filter_regex=".*random *",
            ),
        )
        assert len(comments) == 2
        assert "indeed" in comments[0].body

    def test_pr_comments_author_regex(self):
        comments = list(
            self.project.get_pr(209).get_comments(
                filter_regex=".*nic*",
                author="packit-validator",
            ),
        )
        assert len(comments) == 1
        assert comments[0].author == "packit-validator"
        assert "nicely" in comments[0].body

    def test_pr_comments_author(self):
        comments = list(
            self.project.get_pr(209).get_comments(author="packit-validator"),
        )
        assert len(comments) == 3
        assert comments[0].author == "packit-validator"
        assert comments[0].body.endswith("TM")

    def test_issue_comments_author_regex(self):
        comments = list(
            self.project.get_issue(244).get_comments(
                filter_regex=".*test-*",
                author="packit-validator",
            ),
        )
        assert len(comments) == 1
        assert comments[0].author == "packit-validator"
        assert comments[0].body.startswith("/packit")

    def test_issue_comments_author(self):
        comments = list(
            self.project.get_issue(244).get_comments(author="packit-validator"),
        )

        assert len(comments) == 3
        assert comments[0].author == "packit-validator"
        assert comments[0].body.startswith("/packit")
        assert comments[2].body.endswith("indeed")

    def test_issue_comments_updates(self):
        comments = list(
            self.project.get_issue(244).get_comments(
                filter_regex="test-comment",
            ),
        )
        assert len(comments) == 1
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "here comes the update"
        assert comments[0].body == "here comes the update"

        # using >= because the time difference is so small that the datetime values are the same
        assert comments[0].edited >= before_edited

        comments[0].body = before_comment
        assert comments[0].body == before_comment

    def test_pr_comments_updates(self):
        comments = list(
            self.project.get_pr(209).get_comments(
                filter_regex="nd comment",
            ),
        )
        assert len(comments) == 1
        before_comment = comments[0].body
        before_edited = comments[0].edited

        comments[0].body = "this wont hurt a bit"
        assert comments[0].body == "this wont hurt a bit"

        # using >= because the time difference is so small that the datetime values are the same
        assert comments[0].edited >= before_edited

        comments[0].body = before_comment
        assert comments[0].body == before_comment

    def test_pr_react_to_comment_and_delete(self):
        pr = self.project.get_pr(199)
        pr_comment = pr.comment("React to this comment")

        reaction = pr_comment.add_reaction("+1")
        assert len(pr_comment.get_reactions()) == 1

        reaction.delete()
        assert not reaction._raw_reaction
        assert len(pr_comment.get_reactions()) == 0

    def test_issue_react_to_comment_and_delete(self):
        issue = self.project.get_issue(245)
        issue_comment = issue.comment("This is a nice comment to react to")

        reaction = issue_comment.add_reaction("confused")
        assert len(issue_comment.get_reactions()) == 1

        reaction.delete()
        assert not reaction._raw_reaction
        assert len(issue_comment.get_reactions()) == 0

    def test_pr_get_reactions(self):
        pr = self.project.get_pr(199)
        pr_comment = pr.comment("Such nice weather")

        pr_comment.add_reaction("+1")
        pr_comment.add_reaction("-1")
        pr_comment.add_reaction("confused")
        assert len(pr_comment.get_reactions()) == 3

    def test_issue_get_reactions(self):
        issue = self.project.get_issue(245)
        issue_comment = issue.comment("Nice weather indeed")

        issue_comment.add_reaction("+1")
        issue_comment.add_reaction("-1")
        issue_comment.add_reaction("confused")
        assert len(issue_comment.get_reactions()) == 3

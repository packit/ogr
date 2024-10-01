# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from datetime import datetime

from requre.online_replacing import record_requests_for_all_methods

from tests.integration.gitlab.base import GitlabTests


@record_requests_for_all_methods()
class Comments(GitlabTests):
    def test_pr_react_to_comment_and_delete(self):
        pr = self.service.get_project(repo="playground", namespace="nikromen").get_pr(2)
        pr_comment = pr.comment(datetime.now().strftime("%m/%d/%Y"))

        reaction = pr_comment.add_reaction("+1")
        assert len(pr_comment.get_reactions()) == 1

        reaction.delete()
        assert len(pr_comment.get_reactions()) == 0

    def test_issue_react_to_comment_and_delete(self):
        issue = self.service.get_project(
            repo="playground",
            namespace="nikromen",
        ).get_issue(2)
        issue_comment = issue.comment(datetime.now().strftime("%m/%d/%Y"))

        reaction = issue_comment.add_reaction("tractor")
        assert len(issue_comment.get_reactions()) == 1

        reaction.delete()
        assert len(issue_comment.get_reactions()) == 0

    def test_get_reactions(self):
        pr = self.service.get_project(repo="playground", namespace="nikromen").get_pr(2)
        pr_comment = pr.comment(datetime.now().strftime("%m/%d/%Y"))

        pr_comment.add_reaction("+1")
        pr_comment.add_reaction("-1")
        pr_comment.add_reaction("tractor")
        assert len(pr_comment.get_reactions()) == 3

        issue = self.service.get_project(
            repo="playground",
            namespace="nikromen",
        ).get_issue(2)
        issue_comment = issue.comment(datetime.now().strftime("%m/%d/%Y"))

        issue_comment.add_reaction("+1")
        issue_comment.add_reaction("-1")
        issue_comment.add_reaction("tractor")
        assert len(pr_comment.get_reactions()) == 3

    def test_duplicit_reactions(self):
        pr = self.service.get_project(
            repo="hello-world",
            namespace="packit-service",
        ).get_pr(1149)
        pr_comment = pr.get_comments()[-1]

        pr_reaction_1 = pr_comment.add_reaction("tractor")
        pr_reaction_2 = pr_comment.add_reaction("tractor")
        assert pr_reaction_1._raw_reaction.id == pr_reaction_2._raw_reaction.id

        issue = self.service.get_project(
            repo="hello-world",
            namespace="packit-service",
        ).get_issue(12)
        issue_comment = issue.get_comments()[-1]

        issue_reaction_1 = issue_comment.add_reaction("tractor")
        issue_reaction_2 = issue_comment.add_reaction("tractor")
        assert issue_reaction_1._raw_reaction.id == issue_reaction_2._raw_reaction.id

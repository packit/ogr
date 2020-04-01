from ogr.services.pagure import PagurePullRequest


class TestPullRequest:
    def test_latest_commit(self, data_pagure_raw_pr, pagure_project):
        pagure_pullreqest = PagurePullRequest(
            raw_pr=data_pagure_raw_pr(commit_stop="1a2b3c"), project=pagure_project
        )

        assert pagure_pullreqest.head_commit == "1a2b3c"

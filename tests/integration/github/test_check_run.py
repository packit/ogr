# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from datetime import datetime
from ogr.services.github.check_run import (
    GithubCheckRunResult,
    GithubCheckRunStatus,
    create_github_check_run_output,
)

import pytest
from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base_app import GithubAppTests
from ogr.exceptions import OperationNotSupported
from ogr.services.github import GithubProject


@record_requests_for_all_methods()
class CheckRun(GithubAppTests):
    @property
    def project(self) -> GithubProject:
        return self.hello_world_project

    def test_non_existing_check_runs_returns_none(self):
        check_run = self.project.get_check_run(
            commit_sha="f502aae6920d82948f2dba0b70c9260fb1e34822"
        )

        assert check_run is None

    def test_get_list(self):
        check_runs = self.project.get_check_runs(
            "7cf6d0cbeca285ecbeb19a0067cb243783b3c768"
        )

        assert check_runs
        assert len(check_runs) >= 3

    def test_get_list_no_runs(self):
        check_runs = self.project.get_check_runs(
            "f502aae6920d82948f2dba0b70c9260fb1e34822"
        )
        assert check_runs == []

    def test_create_to_queue_and_succeed(self):
        check_run = self.project.create_check_run(
            name="check run to be queued",
            commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768",
            url="https://localhost",
            external_id="ogr-test",
        )

        assert check_run
        assert check_run.name == "check run to be queued"

        check_run.change_status(conclusion=GithubCheckRunResult.success)

        assert check_run.status == GithubCheckRunStatus.completed
        assert check_run.conclusion == GithubCheckRunResult.success

    def test_create_neutral_completed(self):
        check_run = self.project.create_check_run(
            name="neutral completed",
            commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768",
            url="https://localhost",
            external_id="ogr-test",
            conclusion=GithubCheckRunResult.neutral,
            output=create_github_check_run_output(
                "Compile & run tests",
                "Compilation failed",
                (
                    "# Compile\n\n**FAILED**\n```\nunused parameters\n```\n\n"
                    "# Tests\n\ndependency failed"
                ),
            ),
        )

        assert check_run
        assert check_run.conclusion == GithubCheckRunResult.neutral

    def test_create_timed_out(self):
        check_run = self.project.create_check_run(
            name="timed out",
            commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768",
            url="https://localhost",
            external_id="ogr-test",
            conclusion=GithubCheckRunResult.timed_out,
            output=create_github_check_run_output(
                "Compile & run tests",
                "Tests timed out",
            ),
        )

        assert check_run
        assert check_run.conclusion == GithubCheckRunResult.timed_out

    def test_create_with_completed_without_conclusion(self):
        with pytest.raises(OperationNotSupported):
            self.project.create_check_run(
                name="should fail",
                commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768",
                status=GithubCheckRunStatus.completed,
            )

    def test_create_with_completed_at_without_conclusion(self):
        with pytest.raises(OperationNotSupported):
            self.project.create_check_run(
                name="should fail",
                commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768",
                completed_at=datetime(
                    year=2021, month=5, day=27, hour=11, minute=11, second=11
                ),
            )

    def test_create_completed_without_conclusion(self):
        with pytest.raises(OperationNotSupported):
            self.project.create_check_run(
                name="should fail",
                commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768",
                status=GithubCheckRunStatus.completed,
                completed_at=datetime(
                    year=2021, month=5, day=27, hour=11, minute=11, second=11
                ),
            )

    # these tests need to have at least one check run on given commit
    def test_get_latest_check_run(self):
        check_run = self.project.get_check_run(
            commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768"
        )
        assert check_run

    def test_change_name(self):
        check_run = self.project.get_check_run(
            commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768"
        )
        assert check_run, "No check run exists"

        check_run.name = "New check run name"
        assert check_run.name == "New check run name"

    def test_change_url(self):
        check_run = self.project.get_check_run(
            commit_sha="7cf6d0cbeca285ecbeb19a0067cb243783b3c768"
        )

        assert check_run, "No check run exists"

        check_run.url = "https://packit.dev"
        assert check_run.url == "https://packit.dev"

        check_run.url = "https://dashboard.packit.dev"
        assert check_run.url == "https://dashboard.packit.dev"

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from github.CheckRun import CheckRun
from github.GithubObject import NotSet

from ogr.abstract import OgrAbstractClass
from ogr.exceptions import OperationNotSupported
from ogr.services import github as ogr_github

GithubCheckRunOutput = Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]


class GithubCheckRunStatus(Enum):
    """
    Represents statuses GitHub check run can have.
    """

    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"


class GithubCheckRunResult(Enum):
    """
    Represents conclusion/result of the GitHub check run.
    """

    action_required = "action_required"
    cancelled = "cancelled"
    failure = "failure"
    neutral = "neutral"
    success = "success"
    skipped = "skipped"
    stale = "stale"
    timed_out = "timed_out"


def value_or_NotSet(value: Optional[Any]) -> Any:
    """
    Wrapper for PyGithub, allows us to transform `None` into PyGithub's `NotSet`.

    Args:
        value: Value that can be None.

    Returns:
        If value is not None, value is returned; NotSet otherwise.
    """
    return value if value is not None else NotSet


def create_github_check_run_output(
    title: str,
    summary: str,
    text: Optional[str] = None,
    annotations: Optional[List[Dict[str, Union[str, int]]]] = None,
) -> GithubCheckRunOutput:
    """
    Helper function for constructing valid GitHub output for check run.

    Args:
        title: Title of the output.
        summary: Summary of the output.
        text: Optional text for the output. Can be markdown formatted.

            Defaults to `None`.
        annotations: Optional annotations that are tied to source code.

    Returns:
        Dictionary that represents valid output for check run.
    """
    output: GithubCheckRunOutput = {
        "title": title,
        "summary": summary,
    }

    if text is not None:
        output["text"] = text

    if annotations is not None:
        output["annotations"] = annotations

    return output


class GithubCheckRun(OgrAbstractClass):
    def __init__(
        self, project: "ogr_github.GithubProject", raw_check_run: CheckRun
    ) -> None:
        self.raw_check_run = raw_check_run
        self.project = project

    def __str__(self) -> str:
        return (
            f"GithubCheckRun(project={self.project}, name='{self.name}', "
            f"commit_sha='{self.commit_sha}', "
            f"url='{self.url}', "
            f"external_id='{self.external_id}', "
            f"status={self.status.name}, "
            f"started_at={self.started_at}, "
            f"conclusion={self.conclusion}, "
            f"completed_at={self.completed_at}, "
            f"output={self.output})"
        )

    @property
    def name(self) -> str:
        """Name of the check run."""
        return self.raw_check_run.name

    @name.setter
    def name(self, name: str) -> None:
        self.raw_check_run.edit(name=name)

    @property
    def commit_sha(self) -> str:
        """Commit SHA that check run is related to."""
        return self.raw_check_run.head_sha

    @property
    def url(self) -> Optional[str]:
        """URL with additional details."""
        return self.raw_check_run.details_url

    @url.setter
    def url(self, url: str) -> None:
        self.raw_check_run.edit(details_url=url)

    @property
    def external_id(self) -> Optional[str]:
        """External ID that can be used internally by the integrator."""
        return self.raw_check_run.external_id

    @external_id.setter
    def external_id(self, external_id: str) -> None:
        self.raw_check_run.edit(external_id=external_id)

    @property
    def status(self) -> GithubCheckRunStatus:
        """Current status of the check run."""
        return GithubCheckRunStatus(self.raw_check_run.status)

    @property
    def started_at(self) -> Optional[datetime.datetime]:
        """Timestamp of start of the check run."""
        return self.raw_check_run.started_at

    @started_at.setter
    def started_at(self, started_at: datetime.datetime) -> None:
        self.raw_check_run.edit(started_at=started_at)

    @property
    def conclusion(self) -> GithubCheckRunResult:
        """Conclusion/result of the check run."""
        return GithubCheckRunResult(self.raw_check_run.conclusion)

    @property
    def completed_at(self) -> Optional[datetime.datetime]:
        """Timestamp of completion of the check run."""
        return self.raw_check_run.completed_at

    @property
    def output(self) -> GithubCheckRunOutput:
        """Output of the check run."""
        return self.raw_check_run.output

    @output.setter
    def output(self, output: GithubCheckRunOutput) -> None:
        self.raw_check_run.edit(output=output)

    def change_status(
        self,
        status: Optional[GithubCheckRunStatus] = None,
        completed_at: Optional[datetime.datetime] = None,
        conclusion: Optional[GithubCheckRunResult] = None,
    ) -> None:
        """
        Changes the status of the check run and checks the validity of new state.

        Args:
            status: Status of the check run to be set. If set to completed, you
                must provide conclusion.

                Defaults to `None`.
            completed_at: Timestamp of completion of the check run. If set, you
                must provide conclusion.

                Defaults to `None`.
            conclusion: Conclusion/result of the check run. If only conclusion
                is set, status is automatically set to completed.

                Defaults to `None`.

        Raises:
            OperationNotSupported, if given completed or timestamp of completed
                without conclusion.
        """
        if not (status or completed_at or conclusion):
            return

        if (
            status == GithubCheckRunStatus.completed or completed_at
        ) and conclusion is None:
            raise OperationNotSupported(
                "When provided completed status or completed at,"
                " you need to provide conclusion."
            )

        self.raw_check_run.edit(
            status=value_or_NotSet(status.name if status else None),
            conclusion=value_or_NotSet(conclusion.name if conclusion else None),
            completed_at=value_or_NotSet(completed_at),
        )

    @staticmethod
    def get_list(
        project: "ogr_github.GithubProject",
        commit_sha: str,
        name: Optional[str] = None,
        status: Optional[GithubCheckRunStatus] = None,
    ) -> List["GithubCheckRun"]:
        """
        Returns list of GitHub check runs.

        Args:
            project: Project from which the check runs are retrieved.
            commit_sha: Commit to which are the check runs related to.
            name: Name of the check run for filtering.

                Defaults to `None`, no filtering.
            status: Status of the check runs to be returned.

                Defaults to `None`, no filtering.

        Returns:
            List of the check runs.
        """
        check_runs = project.github_repo.get_commit(commit_sha).get_check_runs(
            check_name=value_or_NotSet(name),
            status=value_or_NotSet(status.name if status else None),
        )

        return [GithubCheckRun(project, run) for run in check_runs]

    @staticmethod
    def get(
        project: "ogr_github.GithubProject",
        check_run_id: Optional[int] = None,
        commit_sha: Optional[str] = None,
    ) -> Optional["GithubCheckRun"]:
        """
        Retrieves GitHub check run as ogr object.

        Args:
            project: Project from which the check run is retrieved.
            check_run_id: Check run ID.

                Defaults to `None`, i.e. is not used for query.
            commit_sha: Commit SHA from which the check run is to be retrieved.
                If set, returns latest check run for the commit.

                Defaults to `None`, i.e. is not used for query.

        Returns:
            GithubCheckRun object or `None` if no check run is found.

        Raises:
            OperationNotSupported, in case there is no parameter for query set
                or both are set.
        """
        if check_run_id is not None and commit_sha:
            raise OperationNotSupported(
                "Cannot retrieve check run by both ID and commit hash"
            )
        elif not (check_run_id is not None or commit_sha):
            raise OperationNotSupported("Cannot retrieve check run by no criteria")

        if check_run_id is not None:
            return GithubCheckRun(
                project, project.github_repo.get_check_run(check_run_id)
            )

        check_runs = project.github_repo.get_commit(commit_sha).get_check_runs()
        if check_runs.totalCount == 0:
            return None
        return GithubCheckRun(project, check_runs[0])

    @staticmethod
    def create(
        project: "ogr_github.GithubProject",
        name: str,
        commit_sha: str,
        url: Optional[str] = None,
        external_id: Optional[str] = None,
        status: GithubCheckRunStatus = GithubCheckRunStatus.queued,
        started_at: Optional[datetime.datetime] = None,
        conclusion: Optional[GithubCheckRunResult] = None,
        completed_at: Optional[datetime.datetime] = None,
        output: Optional[GithubCheckRunOutput] = None,
        actions: Optional[List[Dict[str, str]]] = None,
    ) -> "GithubCheckRun":
        """
        Creates new check run.

        Args:
            project: Project where the check run is to be created.
            name: Name of the check run.
            commit_sha: Hash of the commit that check run is related to.
            url: URL with details of the run.

                Defaults to `None`.
            external_id: External ID that can be used internally by integrator.

                Defaults to `None`.
            status: Status of the check run.

                Defaults to queued.
            started_at: Timestamp of starting the check run.

                Defaults to `None`.
            conclusion: Conclusion of the check run. Should be set with status
                completed.

                Defaults to `None`.
            completed_at: Timestamp of completion of the check run. If set, you
                must provide conclusion.

                Defaults to `None`.
            output: Output of the check run.
            actions: List of possible follow-up actions for the check run.

        Returns:
            Created check run object.

        Raises:
            OperationNotSupported, if given completed status or completion
                timestamp and no conclusion.
        """

        if (
            completed_at or status == GithubCheckRunStatus.completed
        ) and conclusion is None:
            raise OperationNotSupported(
                "When provided completed_at or completed status, "
                "you need to provide conclusion."
            )

        created_check_run = project.github_repo.create_check_run(
            name=name,
            head_sha=commit_sha,
            details_url=value_or_NotSet(url),
            external_id=value_or_NotSet(external_id),
            status=status.name,
            started_at=value_or_NotSet(started_at),
            conclusion=value_or_NotSet(conclusion.name if conclusion else None),
            completed_at=value_or_NotSet(completed_at),
            output=value_or_NotSet(output),
            actions=value_or_NotSet(actions),
        )

        return GithubCheckRun(project, created_check_run)

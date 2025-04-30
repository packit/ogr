# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest
from requre.helpers import record_httpx

from ogr.abstract import MergeCommitStatus, PRStatus
from ogr.exceptions import ForgejoAPIException


@record_httpx()
def test_pr_list(project):
    pr_list = list(project.get_pr_list(status=PRStatus.all))
    assert len({pr.id for pr in pr_list}) > 20


@record_httpx()
def test_pr_info(project):
    pr_info = project.get_pr(pr_id=119)
    assert pr_info.id == 119
    assert pr_info.title == "change"
    assert pr_info.description == "description of mergerequest"
    assert pr_info.url.startswith("https://v10.next.forgejo.org")
    assert pr_info.source_branch == "change"
    assert pr_info.target_branch == "master"
    assert pr_info.status == PRStatus.merged


@record_httpx()
def test_pr_not_exists(project):
    with pytest.raises(ForgejoAPIException):
        project.get_pr(2000)


@record_httpx()
def test_commits_url(project):
    pr = project.get_pr(119)
    assert (
        pr.commits_url
        == "https://v10.next.forgejo.org/packit-validator/ogr-tests/pulls/119/commits"
    )


@record_httpx()
def test_pr_patch(project):
    pr = project.get_pr(119)
    patch = pr.patch
    assert isinstance(patch, bytes)
    assert (
        "From: Laura Barcziova <lbarczio@redhat.com>\nDate: Tue, 10 Sep 2019 15:54:50 +0200\n"
        in patch.decode()
    )


@record_httpx()
def test_get_all_pr_commits(project):
    commits = list(project.get_pr(119).get_all_commits())
    assert commits == [
        "d490ec67dd98f69dfdc1732b98bb3189f0e0aace",
        "3c1fb11dd358254cc3f1588f173e54e98c1d4c09",
    ]


@record_httpx()
def test_pr_labels(project):
    # remove the labels before generating
    pr = project.get_pr(209)
    labels = pr.labels
    assert not labels

    pr.add_label("test_lb1", "test_lb2")
    labels = pr.labels

    assert {label.name for label in labels} >= {"test_lb1", "test_lb2"}


@record_httpx()
def test_head_commit(project):
    assert project.get_pr(119).head_commit == "d490ec67dd98f69dfdc1732b98bb3189f0e0aace"
    assert project.get_pr(137).head_commit == "59b1a9bab5b5198c619270646410867788685c16"


@record_httpx()
def test_target_branch_head_commit(project):
    assert (
        project.get_pr(204).target_branch_head_commit
        == "dd9b6c54c0788301c86bdf058a8e91e3594a0a17"
    )


@record_httpx()
def test_setters(project):
    pr = project.get_pr(119)
    old_title, old_description = pr.title, pr.description
    pr.title = "test title"
    assert pr.title == "test title"
    pr.title = old_title
    pr.description = "test description"
    assert pr.description == "test description"
    pr.description = old_description


@record_httpx()
def test_merge_commit_sha(project):
    pr = project.get_pr(189)
    assert pr.merge_commit_status == MergeCommitStatus.cannot_be_merged
    assert pr.merge_commit_sha == "dd9b6c54c0788301c86bdf058a8e91e3594a0a17"


@record_httpx()
def test_pr_create_upstream_upstream(project):
    pr_opened_before = len(list(project.get_pr_list(status=PRStatus.open)))
    pr = project.create_pr(
        title="test: upstream <- upstream",
        body="pull request body",
        target_branch="master",
        source_branch="readme-change-1",
    )
    pr_opened_after = len(list(project.get_pr_list(status=PRStatus.open)))

    assert pr.title == "test: upstream <- upstream"
    assert pr.status == PRStatus.open
    assert not pr.target_project.is_fork
    assert pr_opened_after == pr_opened_before + 1

    pr.close()
    assert pr.status == PRStatus.closed


@record_httpx()
def test_pr_create_upstream_forkusername(project):
    pr_opened_before = len(list(project.get_pr_list(status=PRStatus.open)))
    pr = project.create_pr(
        title="test: upstream <- fork_username:source_branch",
        body="pull request body",
        target_branch="master",
        source_branch="readme-change-1",
        fork_username="lbarcziova",
    )
    pr_opened_after = len(list(project.get_pr_list(status=PRStatus.open)))

    assert pr.title == "test: upstream <- fork_username:source_branch"
    assert pr.status == PRStatus.open
    assert not pr.target_project.is_fork
    assert pr_opened_after == pr_opened_before + 1

    pr.close()
    assert pr.status == PRStatus.closed


@record_httpx()
def test_pr_create_upstream_fork(project):
    fork_project = project.service.get_project(namespace="lbarcziova", repo="ogr-tests")
    pr_opened_before = len(list(project.get_pr_list(status=PRStatus.open)))
    pr = fork_project.create_pr(
        title="test: upstream <- fork",
        body="pull request body",
        target_branch="master",
        source_branch="readme-change-1",
    )
    pr_opened_after = len(list(project.get_pr_list(status=PRStatus.open)))

    assert pr.title == "test: upstream <- fork"
    assert pr.status == PRStatus.open
    assert not pr.target_project.is_fork
    assert pr_opened_after == pr_opened_before + 1

    pr.close()
    assert pr.status == PRStatus.closed


@record_httpx
def test_pr_create_fork_fork(project):
    fork_project = project.service.get_project(namespace="lbarcziova", repo="ogr-tests")

    pr_opened_before = len(list(fork_project.get_pr_list(status=PRStatus.open)))
    pr = fork_project.create_pr(
        title="test: fork(master) <- fork",
        body="pull request body",
        target_branch="master",
        source_branch="readme-change-1",
        fork_username="lbarcziova",
    )
    pr_opened_after = len(list(fork_project.get_pr_list(status=PRStatus.open)))

    assert pr.title == "test: fork(master) <- fork"
    assert pr.status == PRStatus.open
    assert pr.target_project.is_fork
    assert pr_opened_after == pr_opened_before + 1

    pr.close()
    assert pr.status == PRStatus.closed


@record_httpx()
def test_source_project(project):
    pr = project.get_pr(209)
    assert pr.source_project.repo == "ogr-tests"
    assert pr.source_project.namespace == "packit-validator"
    assert not pr.source_project.is_fork


@record_httpx()
def test_source_project_fork(project):
    pr = project.get_pr(211)
    assert pr.source_project.repo == "ogr-tests"
    assert pr.source_project.namespace == "lbarcziova"
    assert pr.source_project.is_fork

# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest
from requre.helpers import record_httpx

from ogr.abstract import AccessLevel
from ogr.exceptions import ForgejoAPIException


@record_httpx()
def test_get_file_content(project):
    file = project.get_file_content(
        path="README.md",
        ref="b8e18207cfdad954f1b3a96db34d0706b272e6cf",
    )
    assert (
        file == "# ogr-tests\n\nTesting repository for python-ogr package. | "
        "https://github.com/packit-service/ogr\n\ntest1\ntest2\n"
    )


@record_httpx()
def test_get_file_content_resolve_dot(project):
    file = project.get_file_content(
        path="./README.md",
        ref="b8e18207cfdad954f1b3a96db34d0706b272e6cf",
    )
    assert (
        file == "# ogr-tests\n\nTesting repository for python-ogr package. | "
        "https://github.com/packit-service/ogr\n\ntest1\ntest2\n"
    )


@record_httpx()
def test_branches(project):
    branches = project.get_branches()
    assert branches
    assert "master" in set(branches)


@record_httpx()
def test_commits(project):
    commits = list(project.get_commits())
    assert commits
    assert commits[-1] == "24c86d0704694f686329b2ea636c5b7522cfdc40"


@record_httpx()
def test_get_file(project):
    file_content = project.get_file_content("README.md")
    assert file_content
    assert "Testing repository for python-ogr package." in file_content


@pytest.mark.skip(
    reason="Broken API spec resulting in failing validation in pyforgejo (#11)",
)
@record_httpx()
def test_get_files(hello_world_project):
    files = list(hello_world_project.get_files())
    assert files
    assert len(files) >= 1
    assert "README.md" in files

    files = list(hello_world_project.get_files(filter_regex=".*.md"))
    assert files
    assert len(files) >= 1
    assert "README.md" in files


@record_httpx()
def test_nonexisting_file(project):
    with pytest.raises(FileNotFoundError):
        project.get_file_content(".blablabla_nonexisting_file")


@record_httpx()
def test_get_description(project):
    description = project.get_description()
    assert description
    assert description.startswith("Testing repository for python-ogr package.")


@record_httpx()
def test_description_property(project):
    description = project.description
    assert (
        description == "Testing repository for python-ogr package.  |"
        "  https://github.com/packit-service/ogr"
    )


@record_httpx()
def test_description_setter(project):
    old_description = project.description
    assert (
        old_description == "Testing repository for python-ogr package.  |"
        "  https://github.com/packit-service/ogr"
    )

    project.description = "Different description"
    # have to refresh the cached ‹forgejo_repo› after changing the description
    del project.forgejo_repo

    assert project.description == "Different description"

    project.description = old_description
    # have to refresh the cached ‹forgejo_repo› after changing the description
    del project.forgejo_repo

    assert (
        project.description == "Testing repository for python-ogr package.  |"
        "  https://github.com/packit-service/ogr"
    )


@record_httpx()
def test_get_git_urls(project):
    urls = project.get_git_urls()
    assert urls
    assert len(urls) == 2
    assert "git" in urls
    assert "ssh" in urls
    assert urls["git"] == "https://v10.next.forgejo.org/packit-validator/ogr-tests.git"
    assert urls["ssh"].endswith(
        "git@v10.next.forgejo.org:2100/packit-validator/ogr-tests.git",
    )


@record_httpx()
def test_get_sha_from_branch(project):
    commit_sha = project.get_sha_from_branch("change")
    assert commit_sha
    assert commit_sha.startswith("d490ec67")


@record_httpx()
def test_get_sha_from_branch_non_existing(project):
    commit_sha = project.get_sha_from_branch("non-existing")
    assert commit_sha is None


@record_httpx()
def test_get_sha_from_tag(project):
    assert (
        project.get_sha_from_tag("0.1.0") == "24c86d0704694f686329b2ea636c5b7522cfdc40"
    )
    with pytest.raises(ForgejoAPIException) as ex:
        project.get_sha_from_tag("future")
    assert "404" in str(ex.value)


@record_httpx()
def test_parent_project(project):
    assert project.get_fork().parent.namespace == "packit-validator"
    assert project.get_fork().parent.repo == "ogr-tests"


@record_httpx()
def test_get_web_url(project):
    url = project.get_web_url()
    assert url == "https://v10.next.forgejo.org/packit-validator/ogr-tests"


@record_httpx()
def test_full_repo_name(project):
    assert project.full_repo_name == "packit-validator/ogr-tests"


@record_httpx()
def test_project_exists(project):
    assert project.exists()


@record_httpx()
def test_project_not_exists(service):
    assert not service.get_project(
        repo="some-non-existing-repo",
        namespace="some-none-existing-namespace",
    ).exists()


@record_httpx()
def test_is_private(service):
    # when regenerating this test with your forgejo token, use your own private repository
    private_project = service.get_project(
        namespace=service.user.get_username(),
        repo="private",
    )
    assert private_project.is_private()


@record_httpx()
def test_is_not_private(project):
    assert not project.is_private()


@record_httpx()
def test_delete(service):
    project = service.get_project(
        repo="delete-project",
        namespace=service.user.get_username(),
    )
    project.delete()


@record_httpx()
def test_has_issues(service, project):
    assert project.has_issues
    assert not service.get_project(
        namespace="packit-validator",
        repo="test",
    ).has_issues


@record_httpx()
def test_get_owners(project):
    owners = project.get_owners()
    assert owners == ["packit-validator"]


@record_httpx()
def test_get_contributors(project):
    users = project.get_contributors()
    assert users == {"mfocko", "packit-validator"}


@record_httpx()
def test_issue_permissions(project):
    users = project.who_can_close_issue()
    assert "mfocko" in users


@record_httpx()
def test_pr_permissions(project):
    users = project.who_can_merge_pr()
    assert "mfocko" in users
    assert not project.can_merge_pr("lbarcziova")


@record_httpx()
def test_get_users_with_given_access(project):
    maintainers = project.get_users_with_given_access([AccessLevel.maintain])
    assert "packit-validator" in maintainers

    admins = project.get_users_with_given_access([AccessLevel.admin])
    assert "mfocko" in admins


@record_httpx()
def test_add_remove_user(project):
    project.add_user("lbarcziova", AccessLevel.push)
    project.remove_user("lbarcziova")

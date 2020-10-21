from datetime import datetime

import pytest

from ogr.abstract import AccessLevel, CommitStatus
from ogr.exceptions import GitlabAPIException
from requre.online_replacing import record_requests_for_all_methods
from tests.integration.gitlab.base import GitlabTests


@record_requests_for_all_methods()
class GenericCommands(GitlabTests):
    def test_get_file_content(self):
        file = self.project.get_file_content(
            path="README.md", ref="b8e18207cfdad954f1b3a96db34d0706b272e6cf"
        )
        assert (
            file == "# ogr-tests\n\nTesting repository for python-ogr package. | "
            "https://github.com/packit-service/ogr\n\ntest1\ntest2\n"
        )

    def test_request_access(self):
        project = self.service.get_project(
            repo="hello-world", namespace="shreyaspapitest"
        )

        project.request_access()

    def test_add_user(self):
        """
        you can use whatever project what you want, where you have rights to add users
        and user is not already member of project
        :return:
        """
        project = self.service.get_project(repo="ogr-tests", namespace="packit-service")

        project.add_user("tomastomecek", AccessLevel.admin)

    def test_branches(self):
        branches = self.project.get_branches()
        assert branches
        assert "master" in branches

    def test_branches_pagination(self):
        # in time of writing tests using gnuwget/wget2 (28 branches)
        wget_project = self.service.get_project(repo="wget2", namespace="gnuwget")
        branches = wget_project.get_branches()
        assert branches
        assert len(branches) > 20

    def test_get_file(self):
        file_content = self.project.get_file_content("README.md")
        assert file_content
        assert "Testing repository for python-ogr package." in file_content

    def test_get_files(self):
        files = self.project.get_files()
        assert files
        assert len(files) >= 1
        assert "README.md" in files

        files = self.project.get_files(filter_regex=".*.md")
        assert files
        assert len(files) >= 1
        assert "README.md" in files

    def test_nonexisting_file(self):
        with self.assertRaises(FileNotFoundError):
            self.project.get_file_content(".blablabla_nonexisting_file")

    def test_username(self):
        # check just lenght, because it is based who regenerated data files
        assert len(self.service.user.get_username()) > 3

    def test_email(self):
        email = self.service.user.get_email()
        assert email
        assert len(email) > 3
        assert "@" in email
        assert "." in email

    def test_get_description(self):
        description = self.project.get_description()
        assert description
        assert description.startswith("Testing repository for python-ogr package.")

    def test_get_git_urls(self):
        urls = self.project.get_git_urls()
        assert urls
        assert len(urls) == 2
        assert "git" in urls
        assert "ssh" in urls
        assert urls["git"] == "https://gitlab.com/packit-service/ogr-tests.git"
        assert urls["ssh"].endswith("git@gitlab.com:packit-service/ogr-tests.git")

    def test_get_sha_from_tag(self):
        assert (
            self.project.get_sha_from_tag("0.1.0")
            == "24c86d0704694f686329b2ea636c5b7522cfdc40"
        )
        with pytest.raises(GitlabAPIException) as ex:
            self.project.get_sha_from_tag("future")
        assert "not found" in str(ex.value)

    def test_parent_project(self):
        assert self.project.get_fork().parent.namespace == "packit-service"
        assert self.project.get_fork().parent.repo == "ogr-tests"

    def test_get_commit_statuses(self):
        flags = self.project.get_commit_statuses(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64"
        )
        assert isinstance(flags, list)
        assert len(flags) >= 2
        assert flags[0].state == CommitStatus.success
        assert flags[0].comment == "testing status"
        assert flags[0].context == "default"
        assert flags[0].created == datetime(
            year=2019,
            month=9,
            day=18,
            hour=14,
            minute=16,
            second=48,
            microsecond=424000,
        )

    def test_set_commit_status(self):
        old_statuses = self.project.get_commit_statuses(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64"
        )
        status = self.project.set_commit_status(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
            state=CommitStatus.success,
            target_url="https://gitlab.com/packit-service/ogr-tests",
            description="testing status",
            context="test",
        )
        assert status
        new_statuses = self.project.get_commit_statuses(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64"
        )
        assert len(old_statuses) == len(new_statuses)

    def test_commit_comment(self):
        comment = self.project.commit_comment(
            commit="11b37d913374b14f8519d16c2a2cca3ebc14ac64",
            body="Comment to line 3",
            filename="README.md",
            row=3,
        )
        assert comment.author == self.service.user.get_username()
        assert comment.comment == "Comment to line 3"

    def test_get_web_url(self):
        url = self.project.get_web_url()
        assert url == "https://gitlab.com/packit-service/ogr-tests"

    def test_full_repo_name(self):
        assert self.project.full_repo_name == "packit-service/ogr-tests"

    def test_project_exists(self):
        assert self.project.exists()

    def test_project_not_exists(self):
        assert not self.service.get_project(
            repo="some-non-existing-repo", namespace="some-none-existing-namespace"
        ).exists()

    def test_get_owners(self):
        owners = self.project.get_owners()
        assert set(("lachmanfrantisek", "lbarcziova")).issubset(set(owners))

    def test_issue_permissions(self):
        users = self.project.who_can_close_issue()
        assert "lachmanfrantisek" in users
        assert "lbarcziova" in users

        issue = self.project.get_issue(1)
        assert issue.can_close("lachmanfrantisek")
        assert not issue.can_close("not_existing_user")

    def test_pr_permissions(self):
        users = self.project.who_can_merge_pr()
        assert "lachmanfrantisek" in users
        assert "lbarcziova" in users

        assert self.project.can_merge_pr("lachmanfrantisek")
        assert not self.project.can_merge_pr("not_existing_user")

    def test_is_private(self):
        # when regenerating this test with your gitlab token, use your own private repository
        private_project = self.service.get_project(namespace="jscotka", repo="private")
        assert private_project.is_private()

    def test_is_not_private(self):
        assert not self.project.is_private()

    def test_delete(self):
        project = self.service.get_project(
            repo="delete-project", namespace="shreyaspapi"
        )
        project.delete()

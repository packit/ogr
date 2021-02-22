from requre.online_replacing import record_requests_for_all_methods

from tests.integration.gitlab.base import GitlabTests
from ogr.exceptions import OperationNotSupported


@record_requests_for_all_methods()
class Releases(GitlabTests):
    def test_create_release(self):
        try:
            releases_before = self.project.get_releases()
        except OperationNotSupported:
            self.skipTest("This version of python-gitlab does not support releases.")
        version_list = releases_before[0].tag_name.rsplit(".", 1)
        increased = ".".join([version_list[0], str(int(version_list[1]) + 1)])
        count_before = len(releases_before)
        release = self.project.create_release(
            name=f"test {increased}",
            tag_name=increased,
            description=f"testing release-{increased}",
            ref="master",
        )
        count_after = len(self.project.get_releases())
        assert release.tag_name == increased
        assert release.title == f"test {increased}"
        assert release.body == f"testing release-{increased}"
        assert count_before + 1 == count_after

    def test_get_releases(self):
        try:
            releases = self.project.get_releases()
        except OperationNotSupported:
            self.skipTest("This version of python-gitlab does not support releases.")
        assert releases
        count = len(releases)
        assert count >= 1
        assert releases[-1].title == "test"
        assert releases[-1].tag_name == "0.1.0"
        assert releases[-1].body == "testing release"

    def test_get_releases_pagination(self):
        # in time of writing tests using graphviz/graphviz (60 releases)
        graphviz = self.service.get_project(repo="graphviz", namespace="graphviz")
        try:
            releases = graphviz.get_releases()
        except OperationNotSupported:
            self.skipTest("This version of python-gitlab does not support releases.")
        assert releases
        assert len(releases) > 20

    def test_get_latest_release(self):
        try:
            release = self.project.get_releases()[0]
        except OperationNotSupported:
            self.skipTest("This version of python-gitlab does not support releases.")
        latest_release = self.project.get_latest_release()
        assert latest_release.title == release.title
        assert latest_release.tag_name == release.tag_name
        assert latest_release.body == release.body

    def test_get_latest_release_doesnt_exist(self):
        project = self.service.project_create(repo="ogr-playground")
        try:
            assert project.get_latest_release() is None
        except OperationNotSupported:
            self.skipTest("This version of python-gitlab does not support releases.")

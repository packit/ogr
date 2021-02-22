from requre.online_replacing import record_requests_for_all_methods

from tests.integration.github.base import GithubTests


@record_requests_for_all_methods()
class Releases(GithubTests):
    def test_get_release(self):
        release = self.hello_world_project.get_release(tag_name="0.4.1")
        assert release.title == "test"
        assert release.body == "testing release"

    def test_get_releases(self):
        releases = self.ogr_project.get_releases()
        assert releases

        assert len(releases) >= 9

    def test_create_release(self):
        """
        Raise the number in `tag` when regenerating the response files.
        (The `tag` has to be unique.)
        """
        releases_before = self.hello_world_project.get_releases()
        latest_release = releases_before[0].tag_name
        count_before = len(releases_before)
        increased_release = ".".join(
            [
                latest_release.rsplit(".", 1)[0],
                str(int(latest_release.rsplit(".", 1)[1]) + 1),
            ]
        )
        release = self.hello_world_project.create_release(
            tag=increased_release, name="test", message="testing release"
        )
        count_after = len(self.hello_world_project.get_releases())
        assert release.tag_name == increased_release
        assert release.title == "test"
        assert release.body == "testing release"
        assert count_before + 1 == count_after

    def test_edit_release(self):
        release = self.hello_world_project.get_release(tag_name="0.1.0")
        origin_name = release.title
        origin_message = release.body

        release.edit_release(
            name=f"{origin_name}-changed", message=f"{origin_message}-changed"
        )
        assert release.title == f"{origin_name}-changed"
        assert release.body == f"{origin_message}-changed"

    def test_latest_release(self):
        # check the latest release of OGR and fix version and string in the body
        last_version = "0.13.1"
        release = self.ogr_project.get_latest_release()
        assert release.tag_name == last_version
        assert release.title == last_version
        assert "Creating issues in Github" in release.body

    def test_latest_release_doesnt_exist(self):
        project = self.service.project_create(repo="ogr-playground")
        assert project.get_latest_release() is None

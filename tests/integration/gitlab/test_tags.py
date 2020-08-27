from requre.online_replacing import record_requests_for_all_methods

from tests.integration.gitlab.base import GitlabTests


@record_requests_for_all_methods()
class Tags(GitlabTests):
    def test_get_tags(self):
        tags = self.project.get_tags()
        count = len(tags)
        assert count >= 2
        assert tags[count - 1].name == "0.1.0"
        assert tags[count - 1].commit_sha == "24c86d0704694f686329b2ea636c5b7522cfdc40"

    def test_tag_from_tag_name(self):
        tag = self.project._git_tag_from_tag_name(tag_name="0.1.0")
        assert tag.commit_sha == "24c86d0704694f686329b2ea636c5b7522cfdc40"

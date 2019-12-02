import os
import unittest

from ogr import GithubService
from requre.storage import PersistentObjectStorage
from requre.utils import StorageMode

DATA_DIR = "test_data"
PERSISTENT_DATA_PREFIX = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), DATA_DIR
)


class ReadOnly(unittest.TestCase):
    def setUp(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        test_name = self.id() or "all"
        persistent_data_file = os.path.join(
            PERSISTENT_DATA_PREFIX, f"test_github_data_{test_name}.yaml"
        )
        PersistentObjectStorage().storage_file = persistent_data_file
        if PersistentObjectStorage().mode == StorageMode.write and not self.token:
            raise EnvironmentError("please set GITHUB_TOKEN env variables")

        self.service = GithubService(token=self.token, read_only=True)
        self.ogr_project = self.service.get_project(
            namespace="packit-service", repo="ogr"
        )

    def tearDown(self):
        PersistentObjectStorage().dump()

    def test_pr_comments(self):
        pr_comments = self.ogr_project.get_pr_comments(9)
        assert pr_comments
        assert len(pr_comments) == 2

        assert pr_comments[0].body.endswith("fixed")
        assert pr_comments[1].body.startswith("LGTM")

    def test_create_pr(self):
        pr = self.ogr_project.pr_create(
            "title", "text", "master", "lbarcziova:testing_branch"
        )
        assert pr.title == "title"

    def test_create_fork(self):
        fork = self.ogr_project.fork_create()
        assert not fork.is_fork

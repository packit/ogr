# mocking github interface
import github
from ogr.services.mock import core


class MockGitHubProject(core.MockClass):
    mock_class = github.Project.Project
    namespace = "github_project"

    def get_pr_comments(self, *args, **kwargs):
        self.logger.logcall("get_pr_comments", args, kwargs)
        return []


class MockGithub(core.MockClass):
    mock_class = github.Github
    namespace = "github"

    def get_project(self, *args, **kwargs):
        self.logger.logcall("get_project", args, kwargs)
        return MockGitHubProject(*args, **kwargs)

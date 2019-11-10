import pytest
from flexmock import flexmock

from ogr.services.github.project import GithubProject


@pytest.fixture
def github_project(monkeypatch, mock_github_repo):
    github_project = GithubProject(repo='test_repo', service='test_service', namespace='test_namespace')
    parent_github_project = GithubProject(repo='test_parent_repo', service='test_service',
                                          namespace='test_parent_namespace')
    flexmock(github_project)
    flexmock(parent_github_project)

    github_project.should_receive('github_repo').and_return(mock_github_repo())
    parent_github_project.should_receive('github_repo').and_return(mock_github_repo())
    github_project.should_receive('parent').and_return(parent_github_project)
    return github_project


@pytest.fixture
def mock_pull_request():
    def mock_pull_request_factory(pr_id):
        mock = flexmock(id=pr_id)
        return mock

    return mock_pull_request_factory


@pytest.fixture
def mock_github_repo(mock_pull_request):
    def mock_github_repo_factory():
        mock = flexmock(create_pull=mock_pull_request(42))
        return mock

    return mock_github_repo_factory


class TestGithubProject:

    @pytest.mark.parametrize("fork_username",
                             [pytest.param('test_fork_username', id='fork_username_set'),
                              pytest.param(None, id='fork_username_None'), ]
                             )
    def test_pr_create_is_not_fork(self, github_project, fork_username):
        github_project.should_receive('is_fork').and_return(False)
        github_project.should_receive('_pr_from_github_object').and_return()

        head = ':'.join(filter(None, [fork_username, 'source_branch']))

        github_project.github_repo.should_call('create_pull').with_args(title='test_title', body='test_content',
                                                                        base='target_branch', head=head)
        github_project.parent.github_repo.should_call('create_pull').never()
        github_project.github_repo.should_call('create_pull').once()

        github_project.pr_create(title='test_title', body='test_content', target_branch='target_branch',
                                 source_branch='source_branch', fork_username=fork_username)

    @pytest.mark.parametrize("fork_username",
                             [pytest.param('test_fork_username', id='fork_username_set'),
                              pytest.param(None, id='fork_username_None'), ]
                             )
    def test_pr_create_is_fork(self, github_project, fork_username):
        github_project.should_receive('is_fork').and_return(True)
        github_project.should_receive('_pr_from_github_object').and_return()

        github_project.parent.github_repo.should_call('create_pull').with_args(title='test_title', body='test_content',
                                                                               base='target_branch',
                                                                               head=f'{github_project.namespace}:source_branch')

        github_project.parent.github_repo.should_call('create_pull').once()
        github_project.github_repo.should_call('create_pull').never()

        github_project.pr_create(title='test_title', body='test_content', target_branch='target_branch',
                                 source_branch='source_branch', fork_username=fork_username)


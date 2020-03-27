import pytest
from flexmock import flexmock


@pytest.fixture
def mock_pull_request():
    def mock_pull_request_factory(id=42):
        mock = flexmock(id=id)
        return mock

    return mock_pull_request_factory


@pytest.fixture
def mock_github_repo(mock_pull_request):
    def mock_github_repo_factory():
        mock = flexmock(create_pull=mock_pull_request(42))
        return mock

    return mock_github_repo_factory


@pytest.fixture
def mock_pagure_repo(mock_pull_request):
    def mock_pagure_repo_factory():
        mock = flexmock(create_pull=mock_pull_request(42))
        return mock

    return mock_pagure_repo_factory


@pytest.fixture
def data_pagure_raw_pr():
    def data_pagure_raw_pr_factory(commit_stop: int = 123456):
        return {
            "assignee": None,
            "branch": "master",
            "branch_from": "master",
            "cached_merge_status": "FFORWARD",
            "closed_at": None,
            "closed_by": None,
            "comments": [
                {
                    "comment": "comment1",
                    "commit": None,
                    "date_created": "1584877336",
                    "edited_on": None,
                    "editor": None,
                    "filename": None,
                    "id": 149,
                    "line": None,
                    "notification": False,
                    "parent": None,
                    "reactions": {},
                    "tree": None,
                    "user": {
                        "fullname": "J\u00e1n Sak\u00e1lo\u0161",
                        "name": "sakalosj",
                    },
                },
                {
                    "comment": "comment2",
                    "commit": None,
                    "date_created": "1584879440",
                    "edited_on": None,
                    "editor": None,
                    "filename": None,
                    "id": 150,
                    "line": None,
                    "notification": False,
                    "parent": None,
                    "reactions": {},
                    "tree": None,
                    "user": {
                        "fullname": "J\u00e1n Sak\u00e1lo\u0161",
                        "name": "sakalosj",
                    },
                },
            ],
            "commit_start": "aca83b681cabf99061843595203ca1330d866de4",
            "commit_stop": commit_stop,
            "date_created": "1584815643",
            "id": 9,
            "initial_comment": "pr body",
            "last_updated": "1585230213",
            "project": {
                "access_groups": {
                    "admin": ["git-packit-team"],
                    "commit": [],
                    "ticket": [],
                },
                "access_users": {
                    "admin": ["sakalosj"],
                    "commit": [],
                    "owner": ["packit"],
                    "ticket": [],
                },
                "close_status": [],
                "custom_keys": [],
                "date_created": "1584797507",
                "date_modified": "1585301472",
                "description": "packit test repo",
                "fullname": "source-git/packit-hello-world",
                "id": 6843,
                "milestones": {},
                "name": "packit-hello-world",
                "namespace": "source-git",
                "parent": None,
                "priorities": {},
                "tags": [],
                "url_path": "source-git/packit-hello-world",
                "user": {"fullname": "Packit Team", "name": "packit"},
            },
            "remote_git": None,
            "repo_from": {
                "access_groups": {"admin": [], "commit": [], "ticket": []},
                "access_users": {
                    "admin": [],
                    "commit": [],
                    "owner": ["sakalosj"],
                    "ticket": [],
                },
                "close_status": [],
                "custom_keys": [],
                "date_created": "1584799939",
                "date_modified": "1584799939",
                "description": "packit test repo",
                "fullname": "forks/sakalosj/source-git/packit-hello-world",
                "id": 6845,
                "milestones": {},
                "name": "packit-hello-world",
                "namespace": "source-git",
                "parent": {
                    "access_groups": {
                        "admin": ["git-packit-team"],
                        "commit": [],
                        "ticket": [],
                    },
                    "access_users": {
                        "admin": ["sakalosj"],
                        "commit": [],
                        "owner": ["packit"],
                        "ticket": [],
                    },
                    "close_status": [],
                    "custom_keys": [],
                    "date_created": "1584797507",
                    "date_modified": "1585301472",
                    "description": "packit test repo",
                    "fullname": "source-git/packit-hello-world",
                    "id": 6843,
                    "milestones": {},
                    "name": "packit-hello-world",
                    "namespace": "source-git",
                    "parent": None,
                    "priorities": {},
                    "tags": [],
                    "url_path": "source-git/packit-hello-world",
                    "user": {"fullname": "Packit Team", "name": "packit"},
                },
                "priorities": {},
                "tags": [],
                "url_path": "fork/sakalosj/source-git/packit-hello-world",
                "user": {"fullname": "J\u00e1n Sak\u00e1lo\u0161", "name": "sakalosj"},
            },
            "status": "Open",
            "tags": [],
            "threshold_reached": None,
            "title": "pr title",
            "uid": "d54ec33f2ba54730905d3494c677a767",
            "updated_on": "1585230213",
            "user": {"fullname": "J\u00e1n Sak\u00e1lo\u0161", "name": "sakalosj"},
        }

    return data_pagure_raw_pr_factory

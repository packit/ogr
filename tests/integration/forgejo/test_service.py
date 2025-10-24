# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pyforgejo.core.api_error
import pytest
from requre.helpers import record_httpx


@pytest.mark.parametrize(
    "kwargs_",
    [
        pytest.param(
            {"repo": "test", "namespace": "packit"},
            id="create project with specified namespace (organization)",
        ),
        pytest.param(
            {"repo": "test", "namespace": None},
            id="create project without namespace (in the user's namespace)",
        ),
        pytest.param(
            {"repo": "test_1", "namespace": None, "description": "A repo description"},
            id="create project with description",
        ),
    ],
)
@record_httpx()
def test_project_create(service, kwargs_):
    # Construct params for fetching the project
    kwargs_fetch = kwargs_.copy()
    kwargs_fetch["namespace"] = kwargs_fetch["namespace"] or service.user.get_username()

    # Check that project doesn't exist
    project = service.get_project(**kwargs_fetch)
    with pytest.raises(pyforgejo.core.api_error.ApiError):
        _ = project.forgejo_repo

    # Create new project
    new_project = service.project_create(**kwargs_)
    assert new_project.repo == kwargs_["repo"]
    assert new_project.forgejo_repo

    # Try to fetch newly created project
    project = service.get_project(**kwargs_fetch)
    assert project.forgejo_repo

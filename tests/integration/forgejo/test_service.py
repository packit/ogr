# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pyforgejo
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
    user = service.user.get_username()
    kwargs_["user"] = user
    project = service.get_project(**kwargs_)
    with pytest.raises(pyforgejo.core.api_error.ApiError):
        project.forgejo_repo  # noqa: B018

    kwargs_no_user = kwargs_.copy()
    kwargs_no_user.pop("user")
    new_project = service.project_create(**kwargs_no_user)
    assert new_project.repo == kwargs_["repo"]
    assert new_project.forgejo_repo

    project = service.get_project(**kwargs_)
    assert project.forgejo_repo

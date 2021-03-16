from typing import Set

import pytest
from flexmock import Mock
from flexmock import flexmock

from urllib3.util import Retry

from ogr import PagureService, GitlabService, GithubService
from ogr.exceptions import OgrException
from ogr.factory import get_service_class, get_project, get_instances_from_dict
from ogr.services.github import GithubProject
from ogr.services.gitlab import GitlabProject
from ogr.services.pagure import PagureProject


@pytest.mark.parametrize(
    "url,mapping,result",
    [
        ("https://github.com/packit-service/ogr", None, GithubService),
        ("github.com/packit-service/ogr", None, GithubService),
        ("git@github.com:packit-service/ogr.git", None, GithubService),
        (
            "https://some-url/packit-service/ogr",
            {"some-url": GithubService},
            GithubService,
        ),
        (
            "https://github.com/packit-service/ogr",
            {"github.com": PagureService},
            PagureService,
        ),
        ("https://src.fedoraproject.org/rpms/python-ogr", None, PagureService),
        ("https://pagure.io/ogr", None, PagureService),
        ("https://pagure.something.com/ogr", None, PagureService),
        ("https://gitlab.com/someone/project", None, GitlabService),
        ("https://gitlab.abcd.def/someone/project", None, GitlabService),
    ],
)
def test_get_service_class(url, mapping, result):
    service = get_service_class(url=url, service_mapping_update=mapping)
    assert issubclass(result, service)


@pytest.mark.parametrize(
    "url,mapping",
    [
        ("https://unknown.com/packit-service/ogr", None),
        ("unknown.com/packit-service/ogr", None),
        ("git@unknown.com:packit-service/ogr.git", None),
        ("https://unknown/packit-service/ogr", {"some-url": GithubService}),
        ("https://unknown.com/packit-service/ogr", {"github.com": PagureService}),
    ],
)
def test_get_service_class_not_found(url, mapping):
    with pytest.raises(OgrException) as ex:
        _ = get_service_class(url=url, service_mapping_update=mapping)
    assert str(ex.value) == "No matching service was found."


@pytest.mark.parametrize(
    "url,mapping,instances,force_custom_instance,result",
    [
        (
            "https://github.com/packit-service/ogr",
            None,
            None,
            True,
            GithubProject(
                namespace="packit-service", repo="ogr", service=GithubService()
            ),
        ),
        (
            "github.com/packit-service/ogr",
            None,
            None,
            True,
            GithubProject(
                namespace="packit-service", repo="ogr", service=GithubService()
            ),
        ),
        (
            "git@github.com:packit-service/ogr.git",
            None,
            None,
            True,
            GithubProject(
                namespace="packit-service", repo="ogr", service=GithubService()
            ),
        ),
        (
            "https://some-url/packit-service/ogr",
            {"some-url": GithubService},
            None,
            True,
            GithubProject(
                namespace="packit-service", repo="ogr", service=GithubService()
            ),
        ),
        (
            "https://github.com/packit-service/ogr",
            {"github.com": PagureService},
            None,
            True,
            PagureProject(
                namespace="packit-service",
                repo="ogr",
                service=PagureService(instance_url="https://github.com"),
            ),
        ),
        (
            "https://src.fedoraproject.org/rpms/python-ogr",
            None,
            None,
            True,
            PagureProject(
                namespace="rpms",
                repo="python-ogr",
                service=PagureService(instance_url="https://src.fedoraproject.org"),
            ),
        ),
        (
            "https://pagure.io/ogr",
            None,
            None,
            True,
            PagureProject(
                repo="ogr",
                namespace=None,
                service=PagureService(instance_url="https://pagure.io"),
            ),
        ),
        (
            "https://host.name/namespace/project",
            {"host.name": Mock},
            [
                flexmock(
                    instance_url="https://host.name",
                    hostname="host.name",
                    get_project_from_url=lambda url: "project",
                )
            ],
            True,
            "project",
        ),
        (
            "https://host2.name/namespace/project",
            {"host.name": Mock, "host2.name": Mock},
            [
                flexmock(
                    instance_url="https://host.name",
                    hostname="host.name",
                    get_project_from_url=lambda url: "wrong-project",
                ),
                flexmock(
                    instance_url="https://host2.name",
                    hostname="host2.name",
                    get_project_from_url=lambda url: "right-project",
                ),
            ],
            True,
            "right-project",
        ),
        (
            "https://gitlab.gnome.org/lbarcziova/testing-ogr-repo",
            None,
            None,
            True,
            GitlabProject(
                repo="testing-ogr-repo",
                namespace="lbarcziova",
                service=GitlabService(instance_url="https://gitlab.gnome.org"),
            ),
        ),
        (
            "https://src.stg.fedoraproject.org/rpms/python-dockerpty.git",
            None,
            [PagureService(instance_url="https://src.stg.fedoraproject.org")],
            True,
            PagureProject(
                repo="python-dockerpty",
                namespace="rpms",
                service=PagureService(instance_url="https://src.stg.fedoraproject.org"),
            ),
        ),
        (
            "https://src.fedoraproject.org/rpms/python-dockerpty.git",
            None,
            [
                PagureService(instance_url="https://src.stg.fedoraproject.org"),
                PagureService(instance_url="https://src.fedoraproject.org"),
            ],
            False,
            PagureProject(
                repo="python-dockerpty",
                namespace="rpms",
                service=PagureService(instance_url="https://src.fedoraproject.org"),
            ),
        ),
        (
            "https://github.com/packit/ogr",
            None,
            [
                PagureService(instance_url="https://src.fedoraproject.org"),
            ],
            False,
            GithubProject(
                repo="ogr",
                namespace="packit",
                service=GithubService(instance_url="https://github.com/packit/ogr"),
            ),
        ),
    ],
)
def test_get_project(url, mapping, instances, force_custom_instance, result):
    project = get_project(
        url=url,
        service_mapping_update=mapping,
        custom_instances=instances,
        force_custom_instance=force_custom_instance,
    )
    assert project == result


@pytest.mark.parametrize(
    "url,mapping,instances,exc_str",
    [
        (
            "https://unknown.com/packit-service/ogr",
            None,
            None,
            "No matching service was found.",
        ),
        (
            "https://unknown.com/packit-service/ogr",
            {"some-url": GithubService},
            None,
            "No matching service was found.",
        ),
        (
            "https://host.name/namespace/project",
            {"host.name": Mock},
            [
                flexmock(
                    instance_url="https://unknown.com",
                    hostname="unknown.com",
                    get_project_from_url=lambda url: "project",
                )
            ],
            "Instance of type",
        ),
        (
            "https://host.name/namespace/project",
            {"host.name": Mock, "host2.name": Mock},
            [
                flexmock(
                    instance_url="https://host2.name",
                    hostname="host2.name",
                    get_project_from_url=lambda url: "wrong-project",
                ),
                flexmock(
                    instance_url="https://host3.name",
                    hostname="host3.name",
                    get_project_from_url=lambda url: "right-project",
                ),
            ],
            "Instance of type",
        ),
    ],
)
def test_get_project_not_found(url, mapping, instances, exc_str):
    with pytest.raises(OgrException) as ex:
        _ = get_project(
            url=url, service_mapping_update=mapping, custom_instances=instances
        )
    assert exc_str in str(ex.value)


@pytest.mark.parametrize(
    "instances_in_dict,result_instances",
    [
        ({}, set()),
        ({"github.com": {"token": "abcd"}}, {GithubService(token="abcd")}),
        ({"gitlab": {"token": "abcd"}}, {GitlabService(token="abcd")}),
        ({"pagure": {"token": "abcd"}}, {PagureService(token="abcd")}),
        (
            {
                "pagure": {
                    "token": "abcd",
                    "instance_url": "https://src.fedoraproject.org",
                }
            },
            {PagureService(token="abcd", instance_url="https://src.fedoraproject.org")},
        ),
        (
            {"github.com": {"token": "abcd"}, "gitlab": {"token": "abcd"}},
            {GithubService(token="abcd"), GitlabService(token="abcd")},
        ),
        (
            {"github.com": {"github_app_id": "abcd", "github_app_private_key": "efgh"}},
            {GithubService(github_app_id="abcd", github_app_private_key="efgh")},
        ),
        (
            {
                "github.com": {
                    "github_app_id": "abcd",
                    "github_app_private_key_path": "/abc/def/ghi",
                }
            },
            {
                GithubService(
                    github_app_id="abcd", github_app_private_key_path="/abc/def/ghi"
                )
            },
        ),
        (
            {"https://my.gtlb": {"token": "abcd", "type": "gitlab"}},
            {GitlabService(token="abcd", instance_url="https://my.gtlb")},
        ),
        (
            {"github.com": {"tokman_instance_url": "https://localhost"}},
            {GithubService(tokman_instance_url="https://localhost")},
        ),
        (
            {"github.com": {"tokman_instance_url": "http://random.domain.com:8080"}},
            {GithubService(tokman_instance_url="http://random.domain.com:8080")},
        ),
    ],
)
def test_get_instances_from_dict(instances_in_dict, result_instances: Set):
    services = get_instances_from_dict(instances=instances_in_dict)
    assert services == result_instances


@pytest.mark.parametrize(
    "instances_in_dict,result_instances",
    [
        (
            {"github.com": {"token": "abcd", "github_app_id": "123"}},
            {GithubService(github_app_id="123")},
        ),
        (
            {
                "github.com": {
                    "token": "abcd",
                    "tokman_instance_url": "http://localhost",
                },
            },
            {GithubService(tokman_instance_url="http://localhost")},
        ),
        (
            {
                "github.com": {
                    "token": "abcd",
                    "github_app_id": "123",
                    "tokman_instance_url": "http://localhost",
                }
            },
            {GithubService(tokman_instance_url="http://localhost")},
        ),
        (
            {
                "github.com": {
                    "github_app_id": "123",
                    "tokman_instance_url": "http://localhost",
                }
            },
            {GithubService(tokman_instance_url="http://localhost")},
        ),
        (
            {
                "gitlab.com": {
                    "type": "gitlab",
                    "instance_url": "https://gitlab.com",
                    "token": "my_very_secret_token",
                }
            },
            {
                GitlabService(
                    instance_url="https://gitlab.com", token="my_very_secret_token"
                )
            },
        ),
    ],
)
def test_get_instances_from_dict_multiple_auth(instances_in_dict, result_instances):
    assert get_instances_from_dict(instances=instances_in_dict) == result_instances


@pytest.mark.parametrize(
    "instances_in_dict,result_max_retries_total",
    [
        (
            {
                "github.com": {
                    "token": "abcd",
                }
            },
            0,
        ),
        (
            {
                "github.com": {
                    "token": "abcd",
                    "max_retries": "3",
                }
            },
            3,
        ),
        (
            {
                "github.com": {
                    "token": "abcd",
                    "max_retries": 3,
                }
            },
            3,
        ),
        (
            {
                "github.com": {
                    "tokman_instance_url": "http://localhost",
                    "max_retries": 3,
                }
            },
            3,
        ),
        (
            {
                "github.com": {
                    "github_app_id": "123",
                    "max_retries": 3,
                }
            },
            3,
        ),
    ],
)
def test_get_github_instance_with_retries(instances_in_dict, result_max_retries_total):
    instances = get_instances_from_dict(instances_in_dict)

    assert instances
    ghs_instance = instances.pop()
    assert isinstance(ghs_instance, GithubService)
    max_retries = ghs_instance._max_retries
    assert isinstance(max_retries, Retry)
    assert max_retries.total == result_max_retries_total


@pytest.mark.parametrize(
    "instances_in_dict,error_str",
    [
        ({"unknown": {"token": "abcd"}}, "No matching service was found for url"),
        (
            {"https://my.unknown.service": {"token": "abcd", "type": "unknown"}},
            "No matching service was found for type",
        ),
    ],
)
def test_get_instances_from_dict_not_found(instances_in_dict, error_str):
    with pytest.raises(OgrException) as ex:
        _ = get_instances_from_dict(instances=instances_in_dict)
    assert error_str in str(ex.value)

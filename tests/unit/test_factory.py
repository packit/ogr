from typing import Set

import pytest
from flexmock import Mock
from flexmock import flexmock

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
    "url,mapping,instances,result",
    [
        (
            "https://github.com/packit-service/ogr",
            None,
            None,
            GithubProject(
                namespace="packit-service", repo="ogr", service=GithubService()
            ),
        ),
        (
            "github.com/packit-service/ogr",
            None,
            None,
            GithubProject(
                namespace="packit-service", repo="ogr", service=GithubService()
            ),
        ),
        (
            "git@github.com:packit-service/ogr.git",
            None,
            None,
            GithubProject(
                namespace="packit-service", repo="ogr", service=GithubService()
            ),
        ),
        (
            "https://some-url/packit-service/ogr",
            {"some-url": GithubService},
            None,
            GithubProject(
                namespace="packit-service", repo="ogr", service=GithubService()
            ),
        ),
        (
            "https://github.com/packit-service/ogr",
            {"github.com": PagureService},
            None,
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
                    get_project_from_url=lambda url: "project",
                )
            ],
            "project",
        ),
        (
            "https://host2.name/namespace/project",
            {"host.name": Mock, "host2.name": Mock},
            [
                flexmock(
                    instance_url="https://host.name",
                    get_project_from_url=lambda url: "wrong-project",
                ),
                flexmock(
                    instance_url="https://host2.name",
                    get_project_from_url=lambda url: "right-project",
                ),
            ],
            "right-project",
        ),
        (
            "https://gitlab.gnome.org/lbarcziova/testing-ogr-repo",
            None,
            None,
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
            PagureProject(
                repo="python-dockerpty",
                namespace="rpms",
                service=PagureService(instance_url="https://src.fedoraproject.org"),
            ),
        ),
    ],
)
def test_get_project(url, mapping, instances, result):
    project = get_project(
        url=url, service_mapping_update=mapping, custom_instances=instances
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
                    get_project_from_url=lambda url: "wrong-project",
                ),
                flexmock(
                    instance_url="https://host3.name",
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
    ],
)
def test_get_instances_from_dict(instances_in_dict, result_instances: Set):
    services = get_instances_from_dict(instances=instances_in_dict)
    assert services == result_instances


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

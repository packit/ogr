# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import functools
from typing import Dict, Type, Optional, Set, Iterable

from ogr.abstract import GitService, GitProject
from ogr.exceptions import OgrException
from ogr.parsing import parse_git_repo

_SERVICE_MAPPING: Dict[str, Type[GitService]] = {}


def use_for_service(service: str, _func=None):
    """
    Class decorator that adds the class to the service mapping.

    When the project url contains the `service` as a substring,
    this implementation will be used to initialize the project.

    When using this decorator, be sure that your class is initialized.
    (Add the import to ogr/__init__.py )

    Usage:

        @use_for_service("github.com")
        class GithubService(BaseGitService):
            pass

        @use_for_service("pagure.io")
        @use_for_service("src.fedoraproject.org")
        class PagureService(BaseGitService):
            pass

    :param service: str (url of the service)
    """

    def decorator_cover(func):
        @functools.wraps(func)
        def covered_func(kls: Type[GitService]):
            _SERVICE_MAPPING[service] = kls
            return kls

        return covered_func

    return decorator_cover(_func)


def get_project(
    url,
    service_mapping_update: Dict[str, Type[GitService]] = None,
    custom_instances: Iterable[GitService] = None,
    **kwargs,
) -> GitProject:
    """
    Return the project for the given url.

    :param url: str (url of the project, e.g. "https://github.com/packit/ogr")
    :param service_mapping_update: custom mapping from  service url (str) to service class
    :param custom_instances: list of instances that will be used when creating a project instance
    :param kwargs: arguments forwarded to __init__ of the matching service
    :return: GitProject using the matching implementation
    """
    mapping = service_mapping_update.copy() if service_mapping_update else {}
    custom_instances = custom_instances or []
    for instance in custom_instances:
        mapping[instance.instance_url] = instance.__class__

    kls = get_service_class(url=url, service_mapping_update=mapping)
    parsed_repo_url = parse_git_repo(url)

    if custom_instances:
        for service_inst in custom_instances:
            if (
                isinstance(service_inst, kls)
                and service_inst.hostname == parsed_repo_url.hostname
            ):
                service = service_inst
                break
        else:
            raise OgrException(
                f"Instance of type {kls.__name__} "
                f"matching instance url '{url}' was not provided."
            )
    else:
        service = kls(instance_url=parsed_repo_url.get_instance_url(), **kwargs)
    return service.get_project_from_url(url=url)


def get_service_class_or_none(
    url: str, service_mapping_update: Dict[str, Type[GitService]] = None
) -> Optional[Type[GitService]]:
    """
    Get the matching service class from the url.

    :param url: str (url of the project, e.g. "https://github.com/packit/ogr")
    :param service_mapping_update: custom mapping from  service url (str) to service class
    :return: Matched class (subclass of GitService) or None
    """
    mapping = {}
    mapping.update(_SERVICE_MAPPING)
    if service_mapping_update:
        mapping.update(service_mapping_update)

    for service, service_kls in mapping.items():
        if service in url:
            return service_kls

    return None


def get_service_class(
    url: str, service_mapping_update: Dict[str, Type[GitService]] = None
) -> Type[GitService]:
    """
    Get the matching service class from the url.

    :param url: str (url of the project, e.g. "https://github.com/packit/ogr")
    :param service_mapping_update: custom mapping from  service url (str) to service class
    :return: Matched class (subclass of GitService)
    """
    service_kls = get_service_class_or_none(
        url=url, service_mapping_update=service_mapping_update
    )
    if service_kls:
        return service_kls
    raise OgrException("No matching service was found.")


def get_instances_from_dict(instances: dict) -> Set[GitService]:
    """
    Load the service instances from the dictionary in the following form:

    key = hostname, url or name that can be mapped to the service-type
    value = dictionary with arguments used when creating a new instance of the service
            (passed to the `__init__` method)

    e.g.:

    {
        "github.com": {"token": "abcd"},
        "pagure": {
            "token": "abcd",
            "instance_url": "https://src.fedoraproject.org",
        },
    },
    => {
    GithubService(token="abcd"),
    PagureService(token="abcd", instance_url="https://src.fedoraproject.org")
    }

    When the mapping key->service-type is not recognised, you can add a `type` key to the dictionary
    and specify the type of the instance.
    (It can be either name, hostname or url. The used mapping is same as for key->service-type.)

    The provided `key` is used as an `instance_url` and passed to the `__init__` method as well.

    e.g.:

    {
        "https://my.gtlb": {"token": "abcd", "type": "gitlab"},
    },
    => {GitlabService(token="abcd", instance_url="https://my.gtlb")}

    :param instances: mapping from service name/url/hostname to attributes for the service creation
    :return: set of the service instances
    """
    services = set()
    for key, value in instances.items():
        service_kls = get_service_class_or_none(url=key)
        if not service_kls:
            if "type" not in value:
                raise OgrException(
                    f"No matching service was found for url '{key}'. "
                    f"Add the service name as a `type` attribute."
                )
            service_type = value["type"]
            if service_type not in _SERVICE_MAPPING:
                raise OgrException(
                    f"No matching service was found for type '{service_type}'."
                )

            service_kls = _SERVICE_MAPPING[service_type]
            value.setdefault("instance_url", key)
            del value["type"]

        service_instance = service_kls(**value)
        services.add(service_instance)

    return services

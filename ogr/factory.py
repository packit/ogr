# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import functools
import logging
import time
from collections.abc import Iterable
from typing import Optional

from requests.exceptions import ConnectionError, ReadTimeout

from ogr.abstract import GitProject, GitService
from ogr.constant import DGIT_URLS
from ogr.exceptions import OgrException, OgrNetworkError
from ogr.parsing import parse_git_repo

_SERVICE_MAPPING: dict[str, type[GitService]] = {}

# cache dist-git forge service class for two minutes
_DGIT_FORGE_CACHE: dict[str, tuple[float, type[GitService]]] = {}
_DGIT_FORGE_CACHE_TTL = 120

logger = logging.getLogger(__name__)


def use_for_service(service: str, _func=None):
    """
    Class decorator that adds the class to the service mapping.

    When the project url contains the `service` as a substring,
    this implementation will be used to initialize the project.

    When using this decorator, be sure that your class is initialized.
    (Add the import to `ogr/__init__.py`)

    Usage:
    ```py
    @use_for_service("github.com")
    class GithubService(BaseGitService):
        pass

    @use_for_service("pagure.io")
    @use_for_service("git.centos.org")
    class PagureService(BaseGitService):
        pass
    ```

    Args:
        service: URL of the service.

    Returns:
        Decorator.
    """

    def decorator_cover(func):
        @functools.wraps(func)
        def covered_func(kls: type[GitService]):
            _SERVICE_MAPPING[service] = kls
            return kls

        return covered_func

    return decorator_cover(_func)


def get_project(
    url,
    service_mapping_update: Optional[dict[str, type[GitService]]] = None,
    custom_instances: Optional[Iterable[GitService]] = None,
    force_custom_instance: bool = True,
    **kwargs,
) -> GitProject:
    """
    Return the project for the given URL.

    Args:
        url: URL of the project, e.g. `"https://github.com/packit/ogr"`.
        service_mapping_update: Custom mapping from
            service url/hostname (`str`) to service class.

            Defaults to no mapping.
        custom_instances: List of instances that will be
            used when creating a project instance.

            Defaults to `None`.
        force_custom_instance: Force picking a Git service from the
            `custom_instances` list, if there is any provided, raise an error if
            that is not possible.

            Defaults to `True`.
        **kwargs: Arguments forwarded to __init__ of the matching service.

    Returns:
        `GitProject` using the matching implementation.
    """
    mapping = service_mapping_update.copy() if service_mapping_update else {}
    custom_instances = custom_instances or []
    for instance in custom_instances:
        mapping[instance.hostname] = instance.__class__

    kls = get_service_class(url=url, service_mapping_update=mapping)
    parsed_repo_url = parse_git_repo(url)

    service = None
    if custom_instances:
        for service_inst in custom_instances:
            if (
                isinstance(service_inst, kls)
                and service_inst.hostname == parsed_repo_url.hostname
            ):
                service = service_inst
                break
        else:
            if force_custom_instance:
                raise OgrException(
                    f"Instance of type {kls.__name__} "
                    f"matching instance url '{url}' was not provided.",
                )
    if not service:
        service = kls(instance_url=parsed_repo_url.get_instance_url(), **kwargs)
    return service.get_project_from_url(url=url)


def get_service_class_or_none(
    url: str,
    service_mapping_update: Optional[dict[str, type[GitService]]] = None,
) -> Optional[type[GitService]]:
    """
    Get the matching service class from the URL.
    When attempting to get the matching service class for dist-git, probing
    is used to determine whether `PagureService` or `ForgejoService`
    should be returned. This information is cached for two minutes. The
    probing request is set to timeout after 5 seconds.

    Args:
        url: URL of the project, e.g. `"https://github.com/packit/ogr"`.
        service_mapping_update: Custom mapping from service url/hostname (`str`) to service
            class.

            Defaults to `None`.

    Returns:
        Matched class (subclass of `GitService`) or `None`.

    Raises:
        OgrNetworkError, in case a ConnectionError or ReadTimeout error
            is encountered when attempting to probe Pagure dist-git.
    """
    mapping = {}
    mapping.update(_SERVICE_MAPPING)
    non_overridden_dgit_urls: Iterable[str] = DGIT_URLS

    if service_mapping_update:
        mapping.update(service_mapping_update)
        non_overridden_dgit_urls = (
            set(non_overridden_dgit_urls) - service_mapping_update.keys()
        )

    parsed_url = parse_git_repo(url)

    # [XXX] remove once the migration of dist-git is finished
    for dgit_url in non_overridden_dgit_urls:

        # if dealing with dist-git, we need to check whether we need to use
        # `PagureService` or `ForgejoService`
        if dgit_url in parsed_url.hostname:

            from ogr.services.forgejo import ForgejoService
            from ogr.services.pagure import PagureService

            now = time.monotonic()
            if cache := _DGIT_FORGE_CACHE.get(dgit_url):
                timestamp, service_type = cache
                if now - timestamp < _DGIT_FORGE_CACHE_TTL:
                    return service_type
            # API call to the Pagure backend
            api_endpoint = "https://src.fedoraproject.org/api/0/version"
            api_endpoint_stg = "https://src.stg.fedoraproject.org/api/0/version"
            request_url = api_endpoint_stg if ".stg." in dgit_url else api_endpoint

            try:
                pagure_service = PagureService()
                response = pagure_service.get_raw_request(url=request_url, timeout=5)

                # if not found, then dist-git is no longer hosted on Pagure
                dgit_service_kls = (
                    PagureService if response.status_code != 404 else ForgejoService
                )

                _DGIT_FORGE_CACHE[dgit_url] = (now, dgit_service_kls)
                return dgit_service_kls

            except (ConnectionError, ReadTimeout) as er:
                logger.error(er)
                raise OgrNetworkError(f"Cannot connect to url: '{url}'.") from er

    for service, service_kls in mapping.items():
        if parse_git_repo(service).hostname in parsed_url.hostname:
            return service_kls

    return None


def get_service_class(
    url: str,
    service_mapping_update: Optional[dict[str, type[GitService]]] = None,
) -> type[GitService]:
    """
    Get the matching service class from the URL.

    Args:
        url: URL of the project, e.g. `"https://github.com/packit/ogr"`.
        service_mapping_update: Custom mapping from service url/hostname (str) to service
            class.

            Defaults to `None`.

    Returns:
        Matched class (subclass of `GitService`).
    """
    service_kls = get_service_class_or_none(
        url=url,
        service_mapping_update=service_mapping_update,
    )
    if service_kls:
        return service_kls
    raise OgrException("No matching service was found.")


def get_instances_from_dict(instances: dict) -> set[GitService]:
    """
    Load the service instances from the dictionary in the following form:

    - `key`   : hostname, url or name that can be mapped to the service-type
    - `value` : dictionary with arguments used when creating a new instance of the
    service (passed to the `__init__` method)

    e.g.:
    ```py
    get_instances_from_dict({
        "github.com": {"token": "abcd"},
        "forgejo": {
            "token": "abcd",
            "instance_url": "https://src.fedoraproject.org",
        },
    }) == {
        GithubService(token="abcd"),
        ForgejoService(token="abcd", instance_url="https://src.fedoraproject.org")
    }
    ```

    When the mapping `key->service-type` is not recognised, you can add a `type`
    key to the dictionary and specify the type of the instance.
    (It can be either name, hostname or url. The used mapping is same as for
    key->service-type.)

    The provided `key` is used as an `instance_url` and passed to the `__init__`
    method as well.

    e.g.:
    ```py
    get_instances_from_dict({
        "https://my.gtlb": {"token": "abcd", "type": "gitlab"},
    }) == {GitlabService(token="abcd", instance_url="https://my.gtlb")}
    ```

    Args:
        instances: Mapping from service name/url/hostname to attributes for the
            service creation.

    Returns:
        Set of the service instances.
    """
    services = set()
    for key, value in instances.items():
        service_kls = get_service_class_or_none(url=key)
        if not service_kls:
            if "type" not in value:
                raise OgrException(
                    f"No matching service was found for url '{key}'. "
                    f"Add the service name as a `type` attribute.",
                )
            service_type = value["type"]
            if service_type not in _SERVICE_MAPPING:
                raise OgrException(
                    f"No matching service was found for type '{service_type}'.",
                )

            service_kls = _SERVICE_MAPPING[service_type]
            value.setdefault("instance_url", key)
            del value["type"]

        service_instance = service_kls(**value)
        services.add(service_instance)

    return services

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
from typing import Dict, Type, List

from ogr.abstract import GitService, GitProject
from ogr.exceptions import OgrException
from ogr.parsing import parse_git_repo

_SERVICE_MAPPING: Dict[str, Type[GitService]] = {}


def use_for_service(service, _func=None):
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
    custom_instances: List[GitService] = None,
    **kwargs,
) -> GitProject:
    kls = get_service_class(url=url, service_mapping_update=service_mapping_update)

    if custom_instances:
        for service_inst in custom_instances:
            if isinstance(service_inst, kls) and service_inst.instance_url in url:
                service = service_inst
                break
        else:
            raise OgrException(f"Instance of type {kls.__name__} was not provided.")
    else:
        repo_url = parse_git_repo(potential_url=url)
        service = kls(instance_url=repo_url.get_instance_url(), **kwargs)
    project = service.get_project_from_url(url=url)
    return project


def get_service_class(
    url: str, service_mapping_update: Dict[str, Type[GitService]] = None
) -> Type[GitService]:
    mapping = {}
    mapping.update(_SERVICE_MAPPING)
    if service_mapping_update:
        mapping.update(service_mapping_update)

    for service, service_kls in mapping.items():
        if service in url:
            return service_kls
    raise OgrException("No matching service was found.")

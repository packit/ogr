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
from typing import Dict, Type

from ogr.abstract import GitService, GitProject
from ogr.exceptions import OgrException

_SERVICE_MAPPING: Dict[str, Type[GitService]] = {}


def use_for_service(service, _func=None):
    def decorator_cover(func):
        @functools.wraps(func)
        def covered_func(kls: Type[GitService]):
            _SERVICE_MAPPING[service] = kls
            return kls

        return covered_func

    return decorator_cover(_func)


def get_project(url, **kwargs) -> GitProject:
    kls = get_service_class(url=url)
    service = kls(**kwargs)
    project = service.get_project_from_url(url=url)
    return project


def get_service_class(url: str) -> Type[GitService]:
    for service, service_kls in _SERVICE_MAPPING.items():
        if service in url:
            return service_kls
    raise OgrException("No matching service was found.")

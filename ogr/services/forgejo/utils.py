# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from functools import partial


def paginate(api_call, /, *args, **kwargs):
    api_call = partial(api_call, *args, **kwargs)

    page = 1
    while objects := api_call(page=page):
        yield from objects

        page += 1

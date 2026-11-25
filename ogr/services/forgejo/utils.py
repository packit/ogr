# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from functools import partial

from ogr.abstract.exception import catch_common_exceptions


def paginate(api_call, /, *args, **kwargs):
    # The pages are fetched lazily, after the decorated method has returned,
    # so wrap each call to turn pyforgejo errors into ogr exceptions.
    api_call = catch_common_exceptions(partial(api_call, *args, **kwargs))

    page = 1
    while objects := api_call(page=page):
        yield from objects

        page += 1

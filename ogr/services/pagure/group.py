# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging

from ogr.services import pagure as ogr_pagure

logger = logging.getLogger(__name__)


class PagureGroup:
    service: "ogr_pagure.PagureService"

    def __init__(self, name: str, raw_group: dict) -> None:
        self.name = name
        # see https://pagure.io/api/0/#groups-tab
        self._raw_group = raw_group

    def __str__(self) -> str:
        return f'PagureGroup(name="{self.name}")'

    @property
    def members(self) -> list[str]:
        return self._raw_group["members"]

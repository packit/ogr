# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from ogr.abstract.exception import CatchCommonErrors


class OgrAbstractClass(metaclass=CatchCommonErrors):
    def __repr__(self) -> str:
        return f"<{self!s}>"

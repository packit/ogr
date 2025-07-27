# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from enum import Enum


class AuthMethod(str, Enum):
    tokman = "tokman"
    github_app = "github_app"
    token = "token"

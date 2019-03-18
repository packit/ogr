# 0.1.0

* update packit.yaml to reflect packit==0.2.0
* black & Flake8 & mypy fixes
* .pre-commit-config.yaml
* add test and docs for GitHub releases
* Add releases for github
* Jenkinsfile
* Tox
* [Makefile] no sudo
* Enum -> IntEnum
* Move skip_tests() to conftest.py
* create better function to skip tests.
* add skip decorators to skip whole module in case of integration tests in case env vars are not typed
* add packit config

# 0.0.3

## Fixes

* Fix the Python3.6 compatibility:
    * remove dataclasses
    * use strings for type annotations

# 0.0.2

## New Features

* You can now search/filter pull-request comments.
* New methods for changing tokens.
* Basic support for GitHub.
* New method for a file content.

## Breaking changes

* The GitHub repo was moved to the packit-service organization.

## Fixes

* Object representation of the pull-request and pull-request commend.

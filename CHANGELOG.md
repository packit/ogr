# 0.1.0

### New Features

* Ogr now has an API for Github releases.

## Minor

* We have started using black, flake8 and mypy to improve the code quality.

* We are running upstream CI in CentosCI.

* Ogr is using packit to bring upstream releases to Fedora.


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

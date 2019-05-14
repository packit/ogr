# 0.3.0

### New Features

* Mocking of GitHub and Pagure APIs for testing ogr and packit has been greatly improved.
* GithubProject now implements adding of PR comments and also comments and status on a commit.


# 0.2.0

### New Features

* GithubProject now fully supports all the forking-related methods.
* GitProject class now has a parent property to get the original GitProject of
  a fork.
* Methods related to forking received usability updates: they should be now
  easier to work with and you'll need to write less code.
* The upstream project now has a CONTRIBUTING.md file. All your contributions are
  welcome!

## Fixes

* New github pull request now link to the URL on web interface instead of API.

## Minor

* We have implemented multiple tools to increate code quality: coverage, black, pre-commit, mypy, flake8
  * All of them run in CI as well.


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

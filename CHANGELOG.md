# 0.3.0

* add comment why there is little bit confusing assigment
* improve mock pf persistent objects
* use generic exception, to not fail when regenerating
* raise filenotfound exception in pagure method get_file_content
* enable readonly tests
* enable some tests what were disabled when debugging various issues
* check write mode in dump function not in desctructor
* do not flush within desctructor, in case read mode
* avoid to use default flow style for yaml files
* mock pagure classes
* commit status
* Regenerate github test data
* Implement adding PR comments
* commit_comment: Fix typo in docs
* Implement adding commit comments
* method GithubProject().get_sha_from_tag in
* rename github in mock to another name to fix the pypy test
* fix integration test for github by skipping
* add yaml dependency to requirements
* add there class attribute to be possible to use ogr mocking in pagure
* fixed using of open in destructor
* fixed using of open in destructor
* rename write_mode to is_write_mode to be more explicit that there is expected boolean primarily
* add doc strings and adapt PR review comments
* pagure/get_urls: fill in {username}
* use internal keys also in github to be clearer
* mocking also pagure in simplier way
* raise special exception in case key is not in storage file
* move storage class to mock_core
* mock via persistent storage: run integration tests with persistent storage
* adapt jpopelka suggestions from PR
* adapt jpopelka suggestion from PR
* add read only helper and option to github and pagure classes

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

# 0.11.0

## New Features

- Creating of Pagure issues now supports tags. (@cverna)
- Project issues can now be filtered by labels. (@cverna)
- GitProject has new is_private() method. (@dhodovsk)
- Tokens & keys are now obfuscated in logs. (@lachmanfrantisek)
- PR classes now have diff_url property. (@pawelkopka)

## Fixes

- Trailing slash from URLs is now removed before parsing. (@nickcannariato)
- Getting of projects defined with SSH URLs is fixed. (@TomasTomecek)

# 0.10.0

## New Features

- Listing of the issues now supports filtering by author/assignee.
- It is now possible to list files in the remote repository.
- Github project class have a `get_tags` method.
- Issue and pull-request can be edited via properties.

## Fixes

- Fork of the repository contains correct name and namespace after the forking.
- Pagure's `project_create*` was improved.

# 0.9.0

## New Features

- General restructure of the classes thanks to the
  [Red Hat Open Source Contest](https://research.redhat.com/red-hat-open-source-contest/)
  project done by @mfocko.
  _ Classes are better linked together.
  _ Functionality is moved to the classes from the `GitProject` classes.
  _ You can now use the properties (setters) to modify objects.
  _ Old behaviour should work as before, but will raise deprecation warnings.

## Fixes

- Creating of the GitHub pull-requests from the forked repository was fixed. (@sakalosj)

# 0.8.0

## New Features

- GitLab implementation is now feature-complete. (@lbarcziova)
- Added a `get_web_url` method to project classes. (@mfocko)
- Added methods for creating projects to service classes. (@lachmanfrantisek, @mfocko)

## Fixes

- GitHub pull-requests are no longer listed in issue methods. (@mfocko)

## Minor

- Implementations of the `full_repo_name` property were improved. (@mfocko)
- New quickstart example added to the README. (@rpitonak)

# 0.7.0

## New Features

- Introduced a first version of **GitLab** support. (Implementation is not completed yet.) (@lbarcziova)
- Added a method for loading services from dictionary. (@lachmanfrantisek)
- Release objects have a method for editing. (@lbarcziova)
- Added a function for getting all commits from specific PR. (@phracek)

## Fixes

- Fix creating pull-request from fork to upstream on new versions of Pagure. (@lachmanfrantisek)
- Use web url in Pagure issue. (@dustymabe)

## Minor

- Add cryptography to dependencies to be able to authenticate as a github app. (@lachmanfrantisek)
- Add `github_app_private_key_path` parameter to GithubService. (@lachmanfrantisek)
- Make the pagure service mapping more general. (@lachmanfrantisek)
- The tests in CI (zuul) runs both on pip and rpm versions of dependencies. (@lachmanfrantisek)
- We no longer use Centos CI Jenkins. (@jpopelka)
- Run Pagure tests on one repository: https://pagure.io/api/0/ogr-tests. (@lbarcziova)

# 0.6.0

## New Features

- Possibility to authenticate via github-app. (@lachmanfrantisek)
- New method `get_latest_release()` for projects. (@marusinm)
- New method for creating releases in GitHub. (@lbarcziova)
- Add method for getting releases for Pagure. (@lbarcziova)
- Add labels for GitHub pull-requests. (@marusinm)
- New methods for getting pull-request/issue permissions (`who_can_marge_pr`, `who_can_close_issue`, `can_close_issue` and `can_merge_pr`). (@marusinm)
- New methods to get project's owners and permissions of various users. (@marusinm)
- Link GitTag to Release object. (@lbarcziova)
- Add method for creating projects/services from url. (@lachmanfrantisek)
- Creating/closing/commenting Pagure Issues. (@marusinm)

## Fixes

- Correct status handling for Github pull-requests. (@marusinm)
- Fix error 404 on `get_file_content`. (@lbarcziova)

## Minor

- Simplify usage of persistent storage and mocking. (@lachmanfrantisek)
- CommitStatus renamed to CommitFlag. (@lbarcziova)
- Add zuul as a CI system. (@TomasTomecek)
- Removed unused functions. (@lbarcziova)
- Unify external command invocation by subprocess.run. (@lbarcziova)
- Add `__str__` and `__eq__` for classes. (@shreyanshrs44, @lachmanfrantisek)

# 0.5.0

## New Features

- Add support for Github issues. (@marusinm)
- New methods for updating pull-requests. (@lbarcziova)
- New methods for getting forks for user/project. (@lachmanfrantisek)

## Fixes

- Better support for forks and forking. (@lachmanfrantisek)
- Fix a problem when Pagure token is not set. (@lachmanfrantisek)

## Minor

- Write mode in testing is determined whether a respective offline file exists or not. (@lachmanfrantisek)
- Allow saving sequence of responses during tests. (@lachmanfrantisek)

# 0.4.0

- Ogr no longer uses libpagure and calls Pagure API directly.
- PersistentObjectStorage can serialize data into yaml file after calling store().

# 0.3.1

## Fixes

- Added missing module ogr.services.mock

# 0.3.0

### New Features

- Mocking of GitHub and Pagure APIs for testing ogr and packit has been greatly improved.
- GithubProject now implements adding of PR comments and also comments and status on a commit.

# 0.2.0

### New Features

- GithubProject now fully supports all the forking-related methods.
- GitProject class now has a parent property to get the original GitProject of
  a fork.
- Methods related to forking received usability updates: they should be now
  easier to work with and you'll need to write less code.
- The upstream project now has a CONTRIBUTING.md file. All your contributions are
  welcome!

## Fixes

- New github pull request now link to the URL on web interface instead of API.

## Minor

- We have implemented multiple tools to increate code quality: coverage, black, pre-commit, mypy, flake8
  - All of them run in CI as well.

# 0.1.0

### New Features

- Ogr now has an API for Github releases.

## Minor

- We have started using black, flake8 and mypy to improve the code quality.

- We are running upstream CI in CentosCI.

- Ogr is using packit to bring upstream releases to Fedora.

# 0.0.3

## Fixes

- Fix the Python3.6 compatibility:
  - remove dataclasses
  - use strings for type annotations

# 0.0.2

## New Features

- You can now search/filter pull-request comments.
- New methods for changing tokens.
- Basic support for GitHub.
- New method for a file content.

## Breaking changes

- The GitHub repo was moved to the packit-service organization.

## Fixes

- Object representation of the pull-request and pull-request commend.

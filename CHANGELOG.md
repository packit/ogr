# 0.52.1

# 0.52.0

- We have fixed pagination problems in ogr's `GitlabProject.get_commit_comments()`. (#901)

# 0.51.0

- Added base support for forgejo. (#891)

# 0.50.4

- Trigger a new release to confirm the correct SPDX licence.

# 0.50.3

- We have improved wrapping of the forge-specific exceptions, string representation of the original exception is now included. (#884)
- The test suite for parsing git URLs has been extended and also the handling of GitHub repository with changed owner or name has been improved. (#874)

# 0.50.2

- There is a new method for getting a single commit comment, supporting also retrieval and adding reactions in GitHub. (#865)

# 0.50.1

- We have fixed an issue that caused inconsistencies with the expected behavior stated by the documentation when adding duplicate reactions to GitLab comments. (#861)

# 0.50.0

- A new` get_commits` method was implemented for GitHub and Gitlab projects. (#857)
- An issue with silently ignoring error (#760) was fixed. (#855)

# 0.49.2

- `GitLabProject.get_file_content` can now correctly handle file paths starting with `./`. (#844)

# 0.49.1

- Interface for labels was unified and `labels` property for PullRequest and Issue now return list of PRLabel and IssueLabel respectively. (#839)

# 0.49.0

- For Pagure there are 2 new methods available: one for getting users with specified access rights and one for getting members of a group. (#834)

# 0.48.1

- Fix log level and wording when Pagure returns an error while retrieving Pagure PR diffstats.

# 0.48.0

- There is a new get_pr_files_diff method supported for Pagure. (#826)
- We have fixed a bug that GithubRelease.url returned an API URL. (#824)

# 0.47.1

- Fixed an issue where getting a list of GitLab merge requests using `.list()` would return only 20 items. (#819)

# 0.47.0

- Added support for removing users/groups from a project and possibility to check for groups with permissions to modify a PR. (#815)

# 0.46.2

- Added missing README to package metadata.

# 0.46.1

- Migrated from `setup.py` + `setup.cfg` to `pyproject.toml` with `hatchling` as a build backend and to pyproject macros in the spec file. (#808)

# 0.46.0

- We have fixed a bug in `get_fork` method for Pagure about checking the usernames for a match when going through existing forks. (#800)

# 0.45.0

- OGR now supports PyGithub >= 1.58.

# 0.44.0

- OGR now understands a few community-hosted GitLab instances that could not be determined automatically from the hostname. Thanks to that, you don't need to hardcode these instances to be mapped correctly. (#775)

# 0.43.0

- Fixes an issue with project->service mapping where the service with an url not containing the service type wasn't matched. (#771)

# 0.42.0

- A bug in ogr resulting in returning only first page of pull requests for Pagure has been fixed. (#761)
- ogr now raises `GitForgeInternalError` rather than `PagureAPIException` when getting 50x response from the Pagure API. (#762)

# 0.41.0

- `CommitComment.comment` has been deprecated in favour of `CommitComment.body` to make the naming consistent across objects. (#748)
- ogr now requires Python 3.9 or later. (#746)

# 0.40.0

- Using the method `users_with_write_access` you can generate the set of users that have write access to the project and the method `has_write_access(user)` you can find out if the user has write access to the project. (#742)

# 0.39.0

- We have implemented the closed_by property for the Pagure pull request for getting the login of the account that closed the pull request. (#718)

# 0.38.1

- When using Tokman as GitHub authentication mechanism, ogr will now raise GithubAppNotInstalledError instead of failing with generic GithubAPIException when app providing tokens is not installed on the repository.
- Use the standard library instead of setuptools for getting the version on Python 3.8+,
  or a smaller package on older Pythons.
  This also fixes the packaging issue with missing `pkg_resources`.

# 0.38.0

- ogr now correctly raises `OgrException` when given invalid URL to
  `PagureService.get_project_from_url`. (#705)
- We have fixed a bug in ogr that caused `IssueTrackerDisabled` being raised
  only when trying to create an issue on git project with disabled issue
  tracker. Now it is also raised when getting a specific issue or
  an issue list. (#703)

# 0.37.0

- We have added a new optional parameter, `namespace`, to the `fork_create` method on Git projects, which allows you to
  fork a project into a specific namespace. (Forking to namespaces is not allowed on Pagure.) (#685)
- We have implemented a `get_contributors` function that can be used to get the contributors of a GitHub
  (set of logins) and GitLab (set of authors) project. (#692)
- We have introduced a new exception class `GitForgeInternalError` that indicates a failure that happened within the forge
  (indicated via 50x status code). `\*APIException` have been given a new superclass `APIException` that provides status
  code from forge (in case of error, invalid operation, etc.). (#690)
- We have added a new property to git projects, `has_issues`, that indicates whether project has enabled issues or not.
  Following up on the property, `create_issue` now raises `IssueTrackerDisabled` when the project doesn't have issues
  enabled. (#684)

# 0.36.0

- `Release` class has been reworked and `create_release` has been made part of the API for `GitProject`. (#670)
- Factory method for acquiring project or service class from URL has been improved by checking just the hostname for determining the service. (#682)

# 0.35.0

- We have added `target_branch_head_commit` property to the `PullRequest`
  class in `ogr` that allows you to get commit hash of the HEAD of the
  target branch (i.e. base, where the changes are merged to).

# 0.34.0

- We have introduced a new function into `ogr` that allows you to get commit
  SHA of the HEAD of the branch. (#668)
- A list of Gitlab projects provided by `GitlabService.list_projects()` now
  contains objects with additional metadata. (#667)

# 0.33.0

- OGR now fully supports getting PR comments by its ID.

# 0.32.0

- Removal of features which have been marked as deprecated since `0.14.0`.
  - Removal of renamed properties
    - `Comment.comment` -> `Comment.body`
    - `BasePullRequest.project` -> `BasePullRequest.target_project`
  - Removal of methods for accessing issues or pull requests from `GitProject` class.
  - String can no longer be used as commit status, `CommitStatus` is now required.
  - `PullRequest` constructor has been refactored. In order to use static and offline
    representation of a pull request, use `PullRequestReadOnly` instead.
- `GithubCheckRun.app` property has been added for accessing `GithubApp`.

# 0.31.0

- Ogr now catches internal exceptions from Gitlab and Github and converts them
  to ogr exceptions, GitlabAPIException and GithubAPIException, respectively. A
  new exception, OgrNetworkError, has been introduced for signalling situations
  where a request could not be performed due to a network outage. (#642)
- The documentation was converted to Google-style docstrings. (#646)
- Releases and development builds of ogr are now built in copr projects
  packit/packit-dev and packit/packit-releases. (#644)

# 0.30.0

- New method to get pull request and issue comments by their comment ID on
  GitHub and GitLab.

# 0.29.0

- Please check
  [COMPATIBILITY.md](https://github.com/packit/ogr/blob/main/COMPATIBILITY.md)
  to see which methods are implemented for particular services.
- Ogr now supports reacting to a comment (issue, pull request) with a given
  reaction. It's possible to obtain the reactions and delete them (only when
  reaction is added by using ogr API). (#636)

# 0.28.0

- Getting `conclusion` from GitHub's Check Run no longer raises an exception when
  it's not defined, it returns None instead now. (#618)
- When using parsing functions, `pkgs.[stg.]fedoraproject.org` are mapped to
  PagureService. (#620)
- Fix inconsistency of `merge_commit_sha` for GitLab's PRs. (#626)

# 0.27.0

- Implement description get/set property in projects. (#600)
- Support using the merge ref instead of the head ref in a pull request. (#601)
- Implement patch property in GithubPullRequest and GitlabPullRequest. (#613, #614)

# 0.26.0

- Add a function for setting assignees of issues, by [@KPostOffice](https://github.com/KPostOffice), [#589](https://github.com/packit-service/ogr/pull/589)
- 'make check' is now aligned with other Packit projects, by [@bcrocker15](https://github.com/bcrocker15), [#593](https://github.com/packit-service/ogr/pull/593)
- Implement support for GitHub [check runs](https://docs.github.com/en/rest/reference/checks#check-runs), by [@mfocko](https://github.com/mfocko), [#592](https://github.com/packit-service/ogr/pull/592)

# 0.25.0

- Add support for listing of projects in GitLab and Github (by our external
  contributor [@abkosar](https://github.com/abkosar))

# 0.24.1

- Fixed problems with imports from 'gitlab' modules.

# 0.24.0

- Exceptions for non-supported features were refactored.
- Behaviour of Github.get_file_content() was unified with GitLab and Pagure.

# 0.23.0

- Fixed authentication of 'gitlab' type.
- Pagure: enable creating PRs from fork via fork_username.
- Allow ignoring custom instances when creating a project.
- Package is now PEP-561 compliant and mypy is able to use the type information when importing it.

# 0.22.0

## Features

- The retry mechanism of a `GithubService` can be customized using
  `max_retries`. [#537](https://github.com/packit/ogr/pull/537)

## Minor

- `get_latest_release()` returns `None`, instead of raising an exception, when
  there were no release in the project, yet. [#542](https://github.com/packit/ogr/pull/542)

# 0.21.0

## Features

- Implemented `get_files` for Pagure projects (by [@mfocko](https://github.com/mfocko)).

## Minor

- Docs are now being autogenerated, present at https://packit.github.io/ogr (by [@mfocko](https://github.com/mfocko)).

# 0.20.0

## Features

- Add and implement `commits_url` property on pull requests (by [@mfocko](https://github.com/mfocko)).
- Implemented `project.exists` for GitHub projects (by [@path2himanshu](https://github.com/path2himanshu)).

## Minor

- Raise more informative exception for `edited` property on GitLab's commit flag (by [@mfocko](https://github.com/mfocko)).

# 0.19.0

## Features

- Add and implement `GitProject.default_branch` property, by [@jpopelka](https://github.com/jpopelka), [#515](https://github.com/packit-service/ogr/pull/515)
  - All git forges support changing of a default branch of a repo/project. All newly created Github projects have had 'main' as a default branch instead of 'master' [since October 2020](https://docs.github.com/en/free-pro-team@latest/github/administering-a-repository/changing-the-default-branch).
- PagureService: Make retries parametrizable via `max_retries` argument, by [@csomh](https://github.com/csomh), [#514](https://github.com/packit-service/ogr/pull/514)
  - This way users of a PagureService object can control how failures of API calls are retried.

# 0.18.1

## Minor

- Added and polished `__str__` and `__repr__` methods.

## Fixes

- A bug in parsing GitLab URLs with sub-namespace was fixed and parsing was improved.

# 0.18.0

## Features

- Project now have delete functionality (@shreyaspapi).
- Newly created issues can have assignees (@shreyaspapi).

## Minor

- It is now possible to use GitLab annonymously without specifying an authentication token. (@mfocko).

# 0.17.0

## Features

- GitLab projects got the `exists()` method implemented (@lachmanfrantisek).
- It is possible to specify a description when creating projects with
  `project_create()` (@lachmanfrantisek).

## Minor

- When asking for a Pagure user's email address, the error raised explains
  that this is not possible due to the Pagure API not supporting this feature
  (@mfocko).

# 0.16.0

## Features

- Service classes now have `hostname` property (@lachmanfrantisek).

## Internals

- Contribution guide has been updated (@mfocko).
- Tests have been refactored and test data regenerated (@jscotka, @mfocko, @lachmanfrantisek).
  - Minor refactor of `parse_git_repo` (@mfocko).
- README now contains badges for tools that we use (pre-commit, black) (@lachmanfrantisek).

# 0.15.0

## Features

- Add support for repository names with sub-namespaces (multiple slashes) -
  this is possible with GitLab and Pagure (@lachmanfrantisek).

## Minor

- Validate GitHub flag states before setting them - this should give us more
  sensible errors right away (@mfocko).

## Internals

- Ignore type-checking for GitHub App to avoid mypy warnings: short-term
  workaround (@mfocko).
- Update pre-commit configuration and fix mypy remarks (@mfocko).

# 0.14.0

## Minor

- Ogr now uses [tokman](https://github.com/packit/tokman) for authentication
  with Github. (@mfocko)

## Internals

- Authentication related logic has been improved, refactored and
  moved from `GithubProject` to `GithubService`. (@mfocko)

# 0.13.1

## Fixes

- Creating issues in Github (GithubIssue.create) without label works now.

## Internals

- Because of "packit-service -> packit" GitHub organization rename, the required files were updated.
- Documentation now contains [Jupyter examples](https://github.com/packit/ogr/tree/master/examples).

# 0.13.0

## New Features

- Ogr now supports creating private issues for GitLab (known as
  confidential issues) and Pagure.
- Access to GitLab project can be requested via `GitProject.request_access` method.
- You can now add a group to Pagure project.

# 0.12.2

- GitlabPullRequest creates PRs in compliance with documentation. (@mfocko)
- GitlabProject.get_file_content() returns string instead of bytes. (@shreyaspapi)

# 0.12.1

## New Features

- PullRequest can now be created also between two different forks of
  a project. (@mfocko)
- PullRequests have a `patch` property now when working with Pagure. (@jpopelka)
- You can now add collaborators with specific privileges on GitHub and
  GitLab projects. (@shreyaspapi)

## Minor

- When telling if a user can merge PRs in a GitHub repo, ogr asks GitHub
  for the user's permission on the repo instead of checking if the user is
  in the list of collaborators. (@csomh)

## Fixes

- `get_project()` will now correctly use the service instance class for custom.
  service instances. (@lachmanfrantisek)

# 0.12.0

## New Features

- PullRequest now has `source_project`/`target_project` (read-only) properties. (@mfocko)
- GitHub and GitLab now have `head_commit` on PullRequests implemented as well. (@mfocko)

## Minor

- Add git.centos.org to the instances that do not have private repositories. (@csomh)

## Fixes

- Creating PRs to fork now work on GitHub. (@saisankargochhayat)

# 0.11.3

## New Features

- You can now set a title and a description for PagureIssue.

## Fixes

- GitLab classes can now process more than 20 objects (ogr now plays well with the GitLab's pagination mechanism).
- ogr no longer uses backticks in error messages related to Pagure (so they can be displayed nicely in markdown formatting).

## Internals

- Since [rpmautospec](https://docs.pagure.org/Fedora-Infra.rpmautospec/principle.html) is deployed in staging environment only, we have reverted the related changes.

# 0.11.2

## New Features

- A new method to set flags on Pagure PRs was added. (@csomh)
  - It is Pagure-specific.
  - Other git-forges do not have this as they display the flags of the head commit on PRs.
- CommitFlag now has created/edited properties. (@TomasJani)

## Minor

- Pagure service is used for CentOS prod/stg instances by default. (@jsakalos)
- We now forward the specific errors from the Pagure API. (@TomasTomecek)

## Fixes

- Pagination of PR comments on Pagure was fixed. (@AdarLavi)

## Internals

- Tests were removed from the zuul gating pipeline. (@lbarcziova)
- We now use [rpmautospec] for generating changelogs in Fedora. (@TomasTomecek)

[rpmautospec]: https://pagure.io/Fedora-Infra/rpmautospec

# 0.11.1

## New Features

- Added head_commit property to PagurePullrequest. (@jsakalos)

## Fixes

- Packit rev-dep tests were refactored. (@lbarcziova)
- Descriptions in playbooks were fixed. (@lbarcziova)
- GitHubProject raises exception in case of missing install id . (@ttomecek)

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

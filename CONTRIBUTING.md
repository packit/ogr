# Contributing Guidelines

- Please follow common guidelines for our projects [here](https://github.com/packit/contributing).
- Once you are done, please check out our [COMPATIBILITY.md](https://github.com/packit/ogr/blob/main/COMPATIBILITY.md) file and include your changes here (if necessary).

## About ogr

`ogr` provides one Python API for multiple git forges: GitHub, GitLab,
Pagure, and Forgejo. It lets consumers write forge-agnostic code against the
abstract interfaces in `ogr/abstract/`, while each forge has its own concrete
implementation.

## Architecture

`ogr` separates its public, forge-agnostic API from the code that talks to a
specific forge. Consumers should normally work with the abstract interfaces,
not with a GitHub-, GitLab-, Pagure-, or Forgejo-specific class. This keeps a
consumer's code portable across forges and makes unsupported operations
explicit rather than silently relying on one forge's behavior.

The main parts of the codebase are:

- `ogr/abstract/` contains the public abstract base classes, including
  `GitProject`, `GitService`, `PullRequest`, `Issue`, and `Release`. These
  classes define the common contract and documentation for operations that can
  be supported across forges.
- `ogr/services/github/`, `ogr/services/gitlab/`,
  `ogr/services/pagure/`, and `ogr/services/forgejo/` contain concrete
  implementations of the abstract API. Forge-specific request formats,
  response handling, and capability differences belong in these directories.
- `ogr/factory.py` provides the usual forge-agnostic entry points:
  `get_project` creates a project object and `get_service_class` selects the
  matching service implementation from a URL or forge type.
- `ogr/exceptions.py`, `ogr/read_only.py`, `ogr/parsing.py`, and
  `ogr/utils.py` provide cross-cutting functionality shared by services, such
  as exceptions, read-only behavior, parsing helpers, and general utilities.

### Adding or changing an API operation

When adding behavior that should work across forges, start by defining the
method and its semantics on the appropriate class in `ogr/abstract/`. Then
implement that contract in every service that supports it. If a forge cannot
provide the operation, make that limitation explicit and use the established
exception or capability pattern instead of adding a forge-specific shortcut to
the public API.

Keep implementation details inside the relevant service package. A change to a
GitHub API endpoint, for example, belongs under `ogr/services/github/`, while
the public method signature and documented behavior belong in `ogr/abstract/`.
This division is the main guardrail that prevents forge-specific behavior from
leaking into consumer code.

## Reporting Bugs

- [List of known issues](https://github.com/packit/ogr/issues) and in case you need to create a new issue, you can do so [here](https://github.com/packit/ogr/issues/new).
- Getting the version of `ogr`:<br>
  `rpm -q python3-ogr` or `pip3 freeze | grep ogr`

## Documentation

If you want to update documentation, [README.md](README.md) is the file you're looking for.

## Documentation of the services' APIs

Here are some links to the documentation that could be helpful when contributing:

- GitHub (through `PyGithub`)
  - [PyGithub documentation](https://pygithub.readthedocs.io/)
  - for details also see [official GitHub API docs](https://developer.github.com/v3/)
- GitLab (through `Python-Gitlab`)
  - [Python-Gitlab documentation](https://python-gitlab.readthedocs.io/)
  - for details also see [official GitLab API docs](https://docs.gitlab.com/ee/api/)
- Pagure (through `requests`) - API is dependent on deployed version of Pagure service;
  `ogr` is majorly used on (links lead directly to API docs)
  - [pagure.io](https://pagure.io/api/0/)
  - [git.stg.centos.org](https://git.stg.centos.org/api/0/)
- Forgejo
  - [src.fedoraproject.org](https://src.fedoraproject.org/api/v1/)

## Making raw HTTP requests

Before adding support for Forgejo all of our dependencies (`PyGithub`,
`python-gitlab` and our own implementation for Pagure API) used `requests`
library. However with the addition of the Forgejo (`pyforgejo` uses `httpx`), we
have one more library for making HTTP requests, `httpx`.

Please try to follow to conventions of using the same requests library, i.e.,

- GitHub, GitLab, and Pagure implementations use `requests`
- Forgejo implementation uses `httpx`

This makes the handling of tests easier, since there's no need to record
requests from different libraries.

## Testing

Tests are stored in the [tests](/tests) directory.

We recommend running tests in a container. You need to have `podman` or
`docker` installed for this.

To build the test image run:

```
make build-test-image
```

You can run the test now with:

```
make check-in-container
```

The 'make build-test-image' command builds a local image with all the dependencies using
[ansible-bender](https://github.com/ansible-community/ansible-bender);
the 'make check-in-container' command runs the tests in a container created
from that image. `TEST_TARGET` can be set to select a subset of the tests.

NOTE that 'make build-test-image' uses several GB of disk space; consult 'man
containers-storage.conf' for more about container storage
configuration ('make check-in-container' does not use appreciably more
storage).

As a CI we use [Zuul](https://softwarefactory-project.io/zuul/t/local/builds?project=packit-service/ogr) with a configuration in [.zuul.yaml](.zuul.yaml).
If you want to re-run CI/tests in a pull request, just include `recheck` in a comment.

When running the tests we use the pregenerated responses that are saved in ./tests/integration/test_data.
If you need to generate a new file, just run the tests and provide environment variables for the service, e.g. `GITHUB_TOKEN`, `GITLAB_TOKEN`, `PAGURE_TOKEN`, `FORGEJO_TOKEN`. Some API endpoints of Pagure require setting up token for a project: `PAGURE_OGR_TEST_TOKEN`.
The missing file will be automatically generated from the real response. Do not forget to commit the file as well.

If you need to regenerate a response file, just remove it and rerun the tests.
(There are Makefile targets for removing the response files: `remove-response-files`, `remove-response-files-github`, `remove-response-files-gitlab`, `remove-response-files-pagure`, `remove-response-files-forgejo`.)

In case you (re)generate response files, don't forget to run `pre-commit` that includes cleanup of response files.

Running tests locally:

`make check` is also available to run the tests in the environment of your
choice, but first you'll need to make sure to install all the package and test
dependencies, starting with python3-requre and python3-flexmock.
For now it is up to the reader to figure out how to do this on
their system.

## Makefile

### Requirements

- [podman](https://github.com/containers/libpod)
- [ansible-bender](https://pypi.org/project/ansible-bender)
- [buildah](https://github.com/containers/buildah)

### Targets

Here are some important and useful targets of [Makefile](/Makefile):

Use [ansible-bender](https://pypi.org/project/ansible-bender) to build container image from [recipe.yaml](recipe.yaml):

```
make build-test-image
```

Start shell in a container from the image previously built with `make build-test-image`:

```
make shell
```

Run tests in a container:

```
make check-in-container
```

In a container, do basic checks to verify that ogr can be distributed, installed and imported:

```
make check-pypi-packaging
```

Run tests locally:

```
make check
```

______________________________________________________________________

Thank you for your interest!

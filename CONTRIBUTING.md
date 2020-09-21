# Contributing Guidelines

Please follow common guidelines for our projects [here](https://github.com/packit/contributing).

## Reporting Bugs

- [List of known issues](https://github.com/packit/ogr/issues) and in case you need to create a new issue, you can do so [here](https://github.com/packit/ogr/issues/new).
- Getting a version of `ogr`:<br>
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
- Pagure (through `requests`) - API is dependant on deployed version of Pagure service;
  `ogr` is majorly used on (links lead directly to API docs)
  - [src.fedoraproject.org](https://src.fedoraproject.org/api/0/)
  - [pagure.io](https://pagure.io/api/0/)
  - [git.stg.centos.org](https://git.stg.centos.org/api/0/)

## Testing

Tests are stored in [tests](/tests) directory.

We use [Tox](https://pypi.org/project/tox) with configuration in [tox.ini](tox.ini).

Running tests locally:

```
make prepare-check && make check
```

As a CI we use [Zuul](https://softwarefactory-project.io/zuul/t/local/builds?project=packit-service/ogr) with a configuration in [.zuul.yaml](.zuul.yaml).
If you want to re-run CI/tests in a pull request, just include `recheck` in a comment.

When running the tests we are using the pregenerated responses that are saved in the ./tests/integration/test_data.
If you need to generate a new file, just run the tests and provide environment variables for the service, e.g. `GITHUB_TOKEN`, `GITLAB_TOKEN`, `PAGURE_TOKEN`. Some API endpoints of Pagure require setting up token for a project: `PAGURE_OGR_TEST_TOKEN`.
The missing file will be automatically generated from the real response. Do not forget to commit the file as well.

If you need to regenerate a response file, just remove it and rerun the tests.
(There are Makefile targets for removing the response files: `remove-response-files`, `remove-response-files-github`, `remove-response-files-gitlab`, `remove-response-files-pagure`.)

In case you (re)generate response files, don't forget to run `pre-commit` that includes cleanup of response files.

## Makefile

### Requirements

- [podman](https://github.com/containers/libpod)
- [ansible-bender](https://pypi.org/project/ansible-bender)
- [buildah](https://github.com/containers/buildah)

### Targets

Here are some important and useful targets of [Makefile](/Makefile):

Use [ansible-bender](https://pypi.org/project/ansible-bender) to build container image from [recipe.yaml](recipe.yaml):

```
make build
```

Install packages needed to run tests:

```
make prepare-check
```

Run tests locally:

```
make check
```

Start shell in a container from the image previously built with `make build`:

```
make shell
```

In a container, do basic checks to verify that ogr can be distributed, installed and imported:

```
make check-pypi-packaging
```

---

Thank you for your interest!

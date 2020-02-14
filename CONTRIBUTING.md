# Contributing Guidelines

Thanks for your interest in contributing to `ogr`.

The following is a set of guidelines for contributing to `ogr`.
Use your best judgement, and feel free to propose changes to this document in a pull request.

By contributing to this project you agree to the Developer Certificate of Origin (DCO). This document is a simple statement that you, as a contributor, have the legal right to submit the contribution. See the [DCO](DCO) file for details.

## Reporting Bugs

Before creating bug reports, please check a [list of known issues](https://github.com/packit-service/ogr/issues) to see
if the problem has already been reported (or fixed in a master branch).

If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/packit-service/ogr/issues/new).
Be sure to include a **descriptive title and a clear description**. Ideally, please provide:

- version of ogr you are using (`rpm -q python3-ogr` or `pip3 freeze | grep ogr`)
- the command you executed and a debug output (using option `--debug`)

If possible, add a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

**Note:** If you find a **Closed** issue that seems like it is the same thing that you're experiencing, open a new issue and include a link to the original issue in the body of your new one.
You can also comment on the closed issue to indicate that upstream should provide a new release with a fix.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues.
When you are creating an enhancement issue, **use a clear and descriptive title** and **provide a clear description of the suggested enhancement** in as many details as possible.

## Guidelines for Developers

If you would like to contribute code to the `ogr` project, this section is for you!

### Is this your first contribution?

Please take a few minutes to read GitHub's guide on [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/).
It's a quick read, and it's a great way to introduce yourself to how things work behind the scenes in open-source projects.

### Dependencies

If you are introducing a new dependency, please make sure it's added to:

- [setup.cfg](setup.cfg)

### Documentation

If you want to update documentation, [README.md](README.md) is the file you're looking for.

#### Changelog

When you are contributing to changelog, please follow these suggestions:

- The changelog is meant to be read by everyone. Imagine that an average user
  will read it and should understand the changes.
- Every line should be a complete sentence. Either tell what is the change that the tool is doing or describe it precisely:
  - Bad: `Use search method in label regex`
  - Good: `Ogr now uses search method when...`
- And finally, with the changelogs we are essentially selling our projects:
  think about a situation that you met someone at a conference and you are
  trying to convince the person to use the project and that the changelog
  should help with that.

### Testing

Tests are stored in [tests](/tests) directory.

We use [Tox](https://pypi.org/project/tox) with configuration in [tox.ini](tox.ini).

Running tests locally:

```
make prepare-check && make check
```

As a CI we use [Zuul](https://softwarefactory-project.io/zuul/t/local/builds?project=packit-service/ogr) with a configuration in [.zuul.yaml](.zuul.yaml).
If you want to re-run CI/tests in a pull request, just include `recheck` in a comment.

When running the tests we are using the pregenerated responses that are saved in the ./tests/integration/test_data.
If you need to generate a new file, just run the tests and provide environment variables for the service, e.g. `GITHUB_TOKEN`, `GITLAB_TOKEN`, `PAGURE_TOKEN`.
The missing file will be automatically generated from the real response. Do not forget to commit the file as well.

If you need to regenerate a response file, just remove it and rerun the tests.
(There are Makefile targets for removing the response files: `remove-response-files`, `remove-response-files-github`, `remove-response-files-gitlab`, `remove-response-files-pagure`.)

### Makefile

#### Requirements

- [podman](https://github.com/containers/libpod)
- [ansible-bender](https://pypi.org/project/ansible-bender)
- [buildah](https://github.com/containers/buildah)

#### Targets

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

### How to contribute code to ogr

1. Create a fork of this repository.
2. Create a new branch just for the bug/feature you are working on.
3. Once you have completed your work, create a Pull Request, ensuring that it meets the requirements listed below.

### Requirements for Pull Requests (PR)

- Use `pre-commit` (see [below](#checkerslintersformatters--pre-commit)).
- Use common sense when creating commits, not too big, not too small. You can also squash them at the end of review. See [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/).
- Cover new code with a test case (new or existing one).
- All tests have to pass.
- Rebase against updated `master` branch before creating a PR to have linear git history.
- Create a PR against the `master` branch.
- The `mergit` label:
  - Add it to instruct CI and/or reviewer that you're really done with the PR.
  - Anyone else can add it too if they think the PR is ready to be merged.
- Status checks SHOULD all be green.
  - Reviewer(s) have final word and HAVE TO run tests locally if they merge a PR with a red CI.

### Checkers/linters/formatters & pre-commit

To make sure our code is [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant, we use:

- [black code formatter](https://github.com/psf/black)
- [Flake8 code linter](http://flake8.pycqa.org)
- [mypy static type checker](http://mypy-lang.org)

There's a [pre-commit](https://pre-commit.com) config file in [.pre-commit-config.yaml](.pre-commit-config.yaml).
To [utilize pre-commit](https://pre-commit.com/#usage), install pre-commit with `pip3 install pre-commit` and then either:

- `pre-commit install` - to install pre-commit into your [git hooks](https://githooks.com). pre-commit will from now on run all the checkers/linters/formatters on every commit. If you later want to commit without running it, just run `git commit` with `-n/--no-verify`.
- Or if you want to manually run all the checkers/linters/formatters, run `pre-commit run --all-files`.

Thank you for your interest!

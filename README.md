# One Git library to Rule

![PyPI](https://img.shields.io/pypi/v/ogr.svg)
![PyPI - License](https://img.shields.io/pypi/l/ogr.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ogr.svg)
![PyPI - Status](https://img.shields.io/pypi/status/ogr.svg)
[![Build Status](https://zuul-ci.org/gated.svg)](https://softwarefactory-project.io/zuul/t/local/builds?project=packit-service/ogr)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

Library for one API for many git forges. (e.g. GitHub, GitLab, Pagure).

## Currently supported git forges:

- GitHub
- GitLab
- Pagure

## To start using ogr:

See [Documentation of Index of Sub-modules, Functions & Classes](https://packit.github.io/ogr)

For examples of how to use `ogr` see [Jupyter examples](examples).

### GitHub

This snippet shows how to obtain all releases for certain GitHub project using ogr.

```python
from ogr.services.github import GithubService

service = GithubService(token="your_token")

ogr_project = service.get_project(
        repo="ogr",
        namespace="packit-service"
)

ogr_releases = ogr_project.get_releases()


for release in ogr_releases:
    print(release.tag_name)
```

This will output:

```
0.7.0
0.6.0
0.5.0
0.4.0
0.3.1
0.3.0
0.2.0
0.1.0
0.0.3
0.0.2
0.0.1
```

You can use the same API for other forges, you just need to replace `GithubService` with `PagureService`.

## Supported functionality

For more info on functionality that _is not_ supported in all services the same way
see [compatibility tables](COMPATIBILITY.md).

## Installation

On Fedora:

```
$ dnf install python3-ogr
```

You can also use our [`packit-releases` Copr repository](https://copr.fedorainfracloud.org/coprs/packit/packit-releases/)
(contains also released versions of [OGR](https://github.com/packit/ogr)):

```
$ dnf copr enable packit/packit-releases
$ dnf install python3-ogr
```

Or from PyPI:

```
$ pip3 install --user ogr
```

You can also install OGR from `master` branch, if you are brave enough:

You can use our [`packit-master` Copr repository](https://copr.fedorainfracloud.org/coprs/packit/packit-master/)
(contains `master` version of [ogr](https://github.com/packit/ogr)):

```
$ dnf copr enable packit/packit-master
$ dnf install python3-ogr
```

Or

```
$ pip3 install --user git+https://github.com/packit/ogr.git
```

## Requirements

### Makefile

- [podman](https://github.com/containers/libpod)
- [ansible-bender](https://pypi.org/project/ansible-bender)

### Tests

Make sure to install prerequisite packages before first `make check`,
`make build`, or `make check-in-container`. See CONTRIBUTING.md for
details.

# Contribution notes

- Property should not connect to network.

# Contribution guidelines

For more info about contributing to our project see [our contribution guide](/CONTRIBUTING.md).

# Deprecation policy

For more info about deprecation policy see [Deprecation policy](https://github.com/packit/research/tree/master/deprecation)

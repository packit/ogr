# One Git library to Rule [![Build Status](https://zuul-ci.org/gated.svg)](https://softwarefactory-project.io/zuul/t/local/builds?project=packit-service/ogr)

![PyPI](https://img.shields.io/pypi/v/ogr.svg)
![PyPI - License](https://img.shields.io/pypi/l/ogr.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ogr.svg)
![PyPI - Status](https://img.shields.io/pypi/status/ogr.svg)

Library for one API for many git forges. (e.g. GitHub, GitLab, Pagure).

## Currently supported git forges:

- GitHub
- Pagure

## Usage

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

## Requirements

### Makefile

- [podman](https://github.com/containers/libpod)
- [ansible-bender](https://pypi.org/project/ansible-bender)

### Tests

Run `make prepare-check` before first `make check`.

# Contribution notes

- Property should not connect to network.

# Contribution guidelines

For more info about contributing to our project see [our contribution guide](/CONTRIBUTING.md).

# Deprecation policy

For more info about deprecation policy see [Deprecation policy](https://github.com/packit-service/research/tree/master/deprecation)

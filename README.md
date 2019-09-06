# One Git library to Rule [![Build Status](https://zuul-ci.org/gated.svg)](https://softwarefactory-project.io/zuul/t/local/builds?project=packit-service/ogr)

![PyPI](https://img.shields.io/pypi/v/ogr.svg)
![PyPI - License](https://img.shields.io/pypi/l/ogr.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ogr.svg)
![PyPI - Status](https://img.shields.io/pypi/status/ogr.svg)


Library for one API for many git forges. (e.g. GitHub, GitLab, Pagure).

## Currently supported git forges:

- GitHub
- Pagure


## Requirements

### Makefile

- [podman](https://github.com/containers/libpod)
- [ansible-bender](https://pypi.org/project/ansible-bender)

### Tests

Run `make prepare-check` before first `make check`.


# Contribution notes

- Property should not connect to network.


# Contribution guidelines
*  [CONTRIBUTING.md](/CONTRIBUTING.md)

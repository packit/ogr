# One Git library to Rule

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
  - until ansible 2.8 is released, it requires [buildah](https://github.com/containers/buildah)

### Tests

Run `make prepare-check` before first `make check`.


# Contribution notes

- Property should not connect to network.

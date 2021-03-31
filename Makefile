BASE_IMAGE := fedora:latest
TEST_TARGET ?= ./tests/
PY_PACKAGE := ogr
OGR_IMAGE := ogr
IS_FEDORA := $(shell uname -r | grep -c "\.fc[1-9]")
ifeq ($(IS_FEDORA), 1)
    PACKAGE_CHECKER := rpm -q --quiet
    PACKAGE_INSTALLER := dnf install
else
    PACKAGE_CHECKER := :
    PACKAGE_INSTALLER := :
endif

prepare-build:
	if ! $(PACKAGE_CHECKER) ansible-bender ; then sudo $(PACKAGE_INSTALLER) ansible-bender ; fi
	if ! $(PACKAGE_CHECKER) podman ; then sudo $(PACKAGE_INSTALLER) podman ; fi

build: recipe.yaml
	ansible-bender build --build-volumes $(CURDIR):/src:Z -- ./recipe.yaml $(BASE_IMAGE) $(OGR_IMAGE)

prepare-check:
	if ! $(PACKAGE_CHECKER) python3-requre ; then sudo $(PACKAGE_INSTALLER) python3-requre ; fi
	if ! $(PACKAGE_CHECKER) python3-flexmock ; then sudo $(PACKAGE_INSTALLER)  python3-flexmock ; fi

check:
	@#`python3 -m pytest` doesn't work here b/c the way requre overrides import system:
	@#`AttributeError: module 'importlib_metadata' has no attribute 'distributions'
	PYTHONPATH=$(CURDIR) PYTHONDONTWRITEBYTECODE=1 pytest --verbose --showlocals $(TEST_TARGET)

check-in-container:
	podman run --rm -it -v $(CURDIR):/src:Z -w /src $(OGR_IMAGE) make check

shell:
	podman run --rm -ti -v $(CURDIR):/src:Z -w /src $(OGR_IMAGE) bash

check-pypi-packaging:
	podman run --rm -ti -v $(CURDIR):/src:Z -w /src $(OGR_IMAGE) bash -c '\
		set -x \
		&& rm -f dist/* \
		&& python3 ./setup.py sdist bdist_wheel \
		&& pip3 install dist/*.tar.gz \
		&& pip3 show $(PY_PACKAGE) \
		&& twine check ./dist/* \
		&& python3 -c "import ogr; assert ogr.__version__" \
		&& pip3 show -f $(PY_PACKAGE) | ( grep test && exit 1 || :) \
		'

remove-response-files-github:
	rm -rf ./tests/integration/github/test_data/

remove-response-files-pagure:
	rm -rf ./tests/integration/pagure/test_data/

remove-response-files-gitlab:
	rm -rf ./tests/integration/gitlab/test_data/

remove-response-files: remove-response-files-github remove-response-files-pagure remove-response-files-gitlab

requre-purge-files:
	pre-commit run --all-files requre-purge --verbose --hook-stage manual

.PHONY: build

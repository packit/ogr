TEST_IMAGE=ogr-tests

CONTAINER_ENGINE ?= $(shell command -v podman 2> /dev/null || echo docker)
TEST_TARGET ?= ./tests/
PY_PACKAGE := ogr
OGR_IMAGE := ogr
COLOR ?= yes
COV_REPORT ?= --cov=ogr --cov-report=term-missing
SECURITY_OPT=--security-opt label=disable
CONTAINER_RUN_WITH_OPTS=$(CONTAINER_ENGINE) run --rm -ti -v $(CURDIR):/src:Z
CONTAINER_TEST_COMMAND=bash -c "pip3 install .; make -e GITHUB_TOKEN=$(GITHUB_TOKEN) GITLAB_TOKEN=$(GITLAB_TOKEN) FORGEJO_TOKEN=$(FORGEJO_TOKEN) check"

build-test-image:
	$(CONTAINER_ENGINE) build --volume $(CURDIR):/src:Z --rm --tag $(TEST_IMAGE) -f Containerfile.tests .

remove-test-image:
	$(CONTAINER_ENGINE) rmi $(TEST_IMAGE)

check:
	@#`python3 -m pytest` doesn't work here b/c the way requre overrides import system:
	@#`AttributeError: module 'importlib_metadata' has no attribute 'distributions'
	PYTHONPATH=$(CURDIR) PYTHONDONTWRITEBYTECODE=1 python3 /usr/bin/pytest --color=$(COLOR) --verbose --showlocals $(COV_REPORT) $(TEST_TARGET)

check-in-container:
	$(CONTAINER_RUN_WITH_OPTS) $(SECURITY_OPT) \
		--env TEST_TARGET \
		--env COV_REPORT \
		--env COLOR \
		$(TEST_IMAGE) $(CONTAINER_TEST_COMMAND)

shell:
	$(CONTAINER_RUN_WITH_OPTS) -w /src $(TEST_IMAGE) bash

check-pypi-packaging:
	$(CONTAINER_RUN_WITH_OPTS) -w /src $(TEST_IMAGE) bash -c '\
		set -x \
		&& rm -f dist/* \
		&& python3 -m build --sdist --wheel \
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

.PHONY: build-test-image

BASE_IMAGE := fedora:latest
TEST_TARGET ?= ./tests/
PY_PACKAGE := ogr
OGR_IMAGE := ogr

build-test-image: recipe.yaml
	ansible-bender build --build-volumes $(CURDIR):/src:Z -- ./recipe.yaml $(BASE_IMAGE) $(OGR_IMAGE)

check:
	@#`python3 -m pytest` doesn't work here b/c the way requre overrides import system:
	@#`AttributeError: module 'importlib_metadata' has no attribute 'distributions'
	PYTHONPATH=$(CURDIR) PYTHONDONTWRITEBYTECODE=1 pytest --verbose --showlocals $(TEST_TARGET)

check-in-container:
	podman run --rm -it -v $(CURDIR):/src:Z -w /src $(OGR_IMAGE) make -e GITHUB_TOKEN=$(GITHUB_TOKEN) GITLAB_TOKEN=$(GITLAB_TOKEN) check

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

.PHONY: build-test-image

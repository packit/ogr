BASE_IMAGE := registry.fedoraproject.org/fedora:29
TEST_TARGET := ./tests/
PY_PACKAGE := ogr
OGR_IMAGE := ogr

build: recipe.yaml
	ansible-bender build --build-volumes $(CURDIR):/src:Z -- ./recipe.yaml $(BASE_IMAGE) $(OGR_IMAGE)

prepare-check:
	sudo dnf install python3-tox python36

check:
	tox

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

CONFIG_FILE = $(HOME)/.osfv/snipeit.yml
VERSION=$(shell grep '^version =' pyproject.toml | awk -F'\"' '{print $$2}')
PACKAGE_NAME=$(shell grep '^name =' pyproject.toml | awk -F'\"' '{print $$2}')

build:
	poetry build

install: build
	pip install dist/$(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl
	test -f $(CONFIG_FILE) || install -D -m 644 config.yml $(CONFIG_FILE)

uninstall:
	pip uninstall -y $(PACKAGE_NAME)

clean:
	rm -rf dist build $(PACKAGE_NAME).egg-info __pycache__

all: build install

.PHONY: install uninstall build clean

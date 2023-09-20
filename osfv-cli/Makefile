CONFIG_FILE = $(HOME)/.osfv/snipeit.yml
PACKAGE_NAME = snipeit_cli

build:
	poetry build

install: build
	poetry install
	test -f $(CONFIG_FILE) || install -D -m 644 config.yml $(CONFIG_FILE)

uninstall:
	pip uninstall -y $(PACKAGE_NAME)

clean:
	rm -rf dist build $(PACKAGE_NAME).egg-info

all: build install

.PHONY: install uninstall build clean

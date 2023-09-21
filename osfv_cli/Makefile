SNIPEIT_CONFIG_FILE = $(HOME)/.osfv/snipeit.yml
CLI_CONFIG_FILE = $(HOME)/.osfv/cli.yml
ZABBIX_CONFIG_FILE = $(HOME)/.osfv/zabbix.yml
VERSION=$(shell grep '^version =' pyproject.toml | awk -F'\"' '{print $$2}')
PACKAGE_NAME=$(shell grep '^name =' pyproject.toml | awk -F'\"' '{print $$2}')
REPO_ROOT = $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

build:
	poetry build

install: build
	pip install dist/$(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl
	test -f $(SNIPEIT_CONFIG_FILE) || install -D -m 644 snipeit.yml $(SNIPEIT_CONFIG_FILE)
	test -f $(CLI_CONFIG_FILE) || (install -D -m 644 cli.yml $(CLI_CONFIG_FILE) && sed -e 's|MODELS_DIR|$(REPO_ROOT)/models|' -i $(CLI_CONFIG_FILE))
	test -f $(ZABBIX_CONFIG_FILE) || install -D -m 644 zabbix.yml $(ZABBIX_CONFIG_FILE)

uninstall:
	pip uninstall -y $(PACKAGE_NAME)

clean:
	rm -rf dist build $(PACKAGE_NAME).egg-info osfv_cli/__pycache__

all: build install

.PHONY: install uninstall build clean

SNIPEIT_CONFIG_FILE = $(HOME)/.osfv/snipeit.yml
ZABBIX_CONFIG_FILE = $(HOME)/.osfv/zabbix.yml
PACKAGE_NAME=$(shell grep '^name =' pyproject.toml | awk -F'\"' '{print $$2}')
REPO_ROOT = $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

build:
	poetry build

install:
	uv tool install --force .
	test -f $(SNIPEIT_CONFIG_FILE) || install -D -m 644 snipeit.yml $(SNIPEIT_CONFIG_FILE)
	test -f $(ZABBIX_CONFIG_FILE) || install -D -m 644 zabbix.yml $(ZABBIX_CONFIG_FILE)

uninstall:
	uv tool uninstall $(PACKAGE_NAME)

clean:
	rm -rf dist build $(PACKAGE_NAME).egg-info osfv_cli/__pycache__

all: build install

.PHONY: install uninstall build clean

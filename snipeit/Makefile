INSTALL_PATH = /usr/local/bin/snipeit
CONFIG_FILE = $(HOME)/.osfv/snipeit.yml

install:
	sudo install -m 755 snipeit.py /usr/local/bin/snipeit
	test -f $(HOME)/.osfv/snipeit.yml || install -D -m 644 config.yml $(HOME)/.osfv/snipeit.yml

#!/bin/bash

output_file="/usr/lib/zabbix/externalscripts/macros.txt"

touch "$output_file"

if [ -z $1 ]; then
#    echo "No macro provided."
    exit 1
fi

macro_exists() {
    grep -qF "$1" "$output_file"
}

for macro in "$@"; do
    if ! macro_exists "$macro"; then
         echo "$macro" >> "$output_file"
         echo 1
    else
#        echo "Macro '$macro' already exists in the file."
         echo 0
    fi
done

#!/bin/bash

#\/\/\/Change source location\/\/\/
source /usr/lib/zabbix/externalscripts/venv/bin/activate
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

output1=$(osfv_cli snipeit list_used | grep "$1")

if [[ -n "$output1" ]]; then
    echo 3      # TAKEN
else
    output2=$(osfv_cli rte --rte_ip "$1" flash probe)
    if [[ $output2 == *" flash chip "* ]]; then
        echo 1   # Success
    else
        echo 0   # Failure
    fi
fi

deactivate

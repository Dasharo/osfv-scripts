#!/bin/bash

fail="/usr/lib/zabbix/externalscripts/output_fail.txt"
used="/usr/lib/zabbix/externalscripts/output_used.txt"
pass="/usr/lib/zabbix/externalscripts/output_pass.txt"

ip=$1

if grep -qw "$ip" "$fail"; then
   echo 0
elif grep -qw "$ip" "$used"; then
     echo 1
elif grep -qw "$ip" "$pass"; then
     echo 2
fi

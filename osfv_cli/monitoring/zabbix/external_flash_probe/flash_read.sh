#!/bin/bash

output_fail="/usr/lib/zabbix/externalscripts/output_fail.txt"
output_used="/usr/lib/zabbix/externalscripts/output_used.txt"
output_pass="/usr/lib/zabbix/externalscripts/output_pass.txt"

ip=$1

if grep -qw "$ip" "$output_fail"; then
   echo 2
elif grep -qw "$ip" "$output_used"; then
     echo 1
elif grep -qw "$ip" "$output_pass"; then
     echo 0
fi

#!/bin/bash

cd /usr/lib/zabbix/externalscripts/

source /usr/lib/zabbix/externalscripts/venv/bin/activate

input_file="/usr/lib/zabbix/externalscripts/macros.txt"

output_pass="/usr/lib/zabbix/externalscripts/output_pass.txt"
output_fail="/usr/lib/zabbix/externalscripts/output_fail.txt"
output_used="/usr/lib/zabbix/externalscripts/output_used.txt"
stolen="/usr/lib/zabbix/externalscripts/stolen.txt"

> "$output_used"
> "$output_pass"
> "$output_fail"
> "$stolen"

check_snipeit() {
    ip=$1
    if [[ "$ip" =~ [0-9] ]]; then
        if osfv_cli snipeit list_used | grep -qw "$ip"; then
            return 0 # IP is checked out
        else
            osfv_cli snipeit check_out --rte_ip "$ip"
            echo "$ip" >> "$stolen"
            return 1  # IP not checked out
        fi
    else
        return 1  # IP contains no numbers
    fi
}

probe_flash() {
    ip=$1
    output_flash=$(osfv_cli rte --rte_ip "$ip" flash probe)
    if echo "$output_flash" | grep -qE 'Found .* flash chip ".*" \(.*\) on .*\.'; then
        echo "$ip" >> "$output_pass"
    else
        echo "$ip" >> "$output_fail"
    fi
}

while IFS= read -r ip || [ -n "$ip" ]; do
    if check_snipeit "$ip"; then
        echo "$ip found in snipeit list_used"
        echo "$ip" >> "$output_used"
    else
        echo "$ip not found in snipeit list_used, probing flash..."
        probe_flash "$ip"
    fi
done < "$input_file"

while IFS= read -r ip || [ -n "$ip" ]; do
   osfv_cli snipeit check_in --rte_ip "$ip"
done < "$stolen"

deactivate


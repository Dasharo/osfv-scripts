#!/bin/bash
#Output files location
Cd /usr/lib/zabbix/externalscripts/

source /usr/lib/zabbix/externalscripts/venv/bin/activate

#File with IPs to check  -created by flash_write.sh
input_file="/usr/lib/zabbix/externalscripts/macros.txt"

#The file where the IPs that passed 'flash probe' without issues are saved.
output_pass="/usr/lib/zabbix/externalscripts/output_pass.txt"
#The file where the IPs that did not pass 'flash probe' are saved.
output_fail="/usr/lib/zabbix/externalscripts/output_fail.txt"
#The file where the IPs that are currently in use are saved.
output_used="/usr/lib/zabbix/externalscripts/output_used.txt"
#The file where the IPs that are currently stolen bo this script are saved.
stolen="/usr/lib/zabbix/externalscripts/stolen.txt"

rm "$output_used"
rm "$output_pass"
rm "$output_fail"
rm "$stolen"

check_snipeit() {
    ip=$1
    if [[ "$ip" =~ [0-9] ]]; then
        if osfv_cli snipeit check_out --rte_ip "$ip" | grep -qw "successfully checked out."; then
            return 0 #ip successfully checked out
        else
            return 3 #failed to check out
        fi
    else
        return 2 # IP contains no numbers
    fi
}

probe_flash() {
    ip=$1
    output_flash=$(osfv_cli rte --rte_ip "$ip" flash probe)
    if echo "$output_flash" | grep -qE 'Found .* flash chip ".*" \(.*\) on .*\.'; then
        echo "$ip" >> "$output_pass"
        return 0
    else
        echo "$ip" >> "$output_fail"
        return 1
    fi
}

while IFS= read -r ip || [ -n "$ip" ]; do
    if check_snipeit "$ip"; then
        echo "$ip successfully checked out, probing flash..."
        probe_flash "$ip"
        osfv_cli snipeit check_in --rte_ip "$ip"
        return 0
    else
        echo "Failed to checkout $ip ._."
        echo "$ip" >> "$output_used"
        return 3 #Failed to check out IP
    fi
done < "$input_file"
deactivate

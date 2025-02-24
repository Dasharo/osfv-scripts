*** Settings ***
Documentation       Common keywords to be used during osfv_cli testing

Library             Process


*** Variables ***
${RTE_IP_APU2}=         192.168.10.172
${ASSET_ID_APU2}=       31

${RTE_IP_FW4C}=         192.168.10.168
${ASSET_ID_FW4C}=       42

${RTE_IP_V1410}=        192.168.10.198

${RTE_IP_VP4630}=       192.168.10.244

${RTE_IP_Z690}=         192.168.10.199


*** Keywords ***
Run Flash Probe
    [Arguments]    ${ip}
    ${result}=    Run Process    osfv_cli    rte    --rte_ip    ${ip}    flash    probe
    Should Not Match    ${result.stdout}    *No EEPROM/flash device found.*
    Should Match    ${result.stdout}    *Found * flash chip * on *
    Should Be Equal As Integers    ${result.rc}    0
    Should Be Empty    ${result.stderr}
    RETURN    ${result}

Check In Test Devices
    Check In    ${RTE_IP_APU2}
    Check In    ${RTE_IP_V1410}
    Check In    ${RTE_IP_VP4630}
    Check In    ${RTE_IP_Z690}
    Check In    ${RTE_IP_FW4C}

Check Out
    [Documentation]    Check out asset using osfv_cli as user defined in ~/.osfv.snipeit.yml
    [Arguments]    ${rte_ip}    ${snipeit_config}=%{HOME}/.osfv/snipeit.yml
    ${result}=    Run Process
    ...    osfv_cli
    ...    snipeit
    ...    check_out
    ...    --rte_ip
    ...    ${rte_ip}
    ...    env:SNIPEIT_CONFIG_FILE_PATH=${snipeit_config}
    Log    ${snipeit_config}
    Log    ${result.stdout}
    Log    ${result.stderr}
    RETURN    ${result}

Check Out By Asset ID
    [Documentation]    Check out asset using osfv_cli as user defined
    ...    in ~/.osfv.snipeit.yml
    [Arguments]    ${asset_id}    ${snipeit_config}=%{HOME}/.osfv/snipeit.yml
    ${result}=    Run Process
    ...    osfv_cli
    ...    snipeit
    ...    check_out
    ...    --asset_id
    ...    ${asset_id}
    ...    env:SNIPEIT_CONFIG_FILE_PATH=${snipeit_config}
    Log    ${snipeit_config}
    Log    ${result.stdout}
    Log    ${result.stderr}
    RETURN    ${result}

Check In
    [Documentation]    Check in asset using osfv_cli as user defined in ~/.osfv.snipeit.yml
    [Arguments]    ${rte_ip}    ${snipeit_config}=%{HOME}/.osfv/snipeit.yml
    ${result}=    Run Process
    ...    osfv_cli
    ...    snipeit
    ...    check_in
    ...    --rte_ip
    ...    ${rte_ip}
    ...    env:SNIPEIT_CONFIG_FILE_PATH=${snipeit_config}
    Log    ${result.stdout}
    Log    ${result.stderr}
    RETURN    ${result}

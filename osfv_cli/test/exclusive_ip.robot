*** Settings ***
Documentation       IP duplication protection (IP, RTE IP, Sonoff IP, PiKVM IP) test suite.

Library             Process
Resource            ../test/common/keywords.robot


*** Variables ***
${UNIT_00_ID}=              226
${UNIT_01_ID}=              227
${UNIT_02_ID}=              228
${UNIT_03_ID}=              229

${UNIT_00_IP}=              127.1.0.1
${UNIT_01_IP}=              127.1.1.1
${UNIT_02_IP}=              127.1.2.1
${UNIT_03_IP}=              127.1.0.1

${UNIT_00_RTE_IP}=          127.100.1.1
${UNIT_01_RTE_IP}=          127.100.1.1
${UNIT_02_RTE_IP}=          127.100.2.1
${UNIT_03_RTE_IP}=          127.100.1.1

${UNIT_00_SONOFF_IP}=       127.7.0.1
${UNIT_01_SONOFF_IP}=       127.7.1.1
${UNIT_02_SONOFF_IP}=       127.7.0.1
${UNIT_03_SONOFF_IP}=       127.7.0.1

${UNIT_00_PIKVM_IP}=        127.200.1.1
${UNIT_01_PIKVM_IP}=        127.200.1.1
${UNIT_02_PIKVM_IP}=        127.200.1.1
${UNIT_03_PIKVM_IP}=        127.200.1.1

${BY_RTE_FAILURE_PRE}=      SEPARATOR=    osfv.libs.snipeit_api.SnipeIT.
...                         DuplicatedIpException: FATAL: You are trying to access an asset with
${BY_RTE_FAILURE_POST}=     SEPARATOR=    which is not exclusive. Please check Snipe-IT data.


*** Test Cases ***    ***
Check Out By RTE IP Negative failing on RTE IP
    [Documentation]    Should fail due to RTE IP non-exclusivity
    ${checkout_result}=    Check Out    rte_ip=${UNIT_00_RTE_IP}

    ${expected}=    Catenate    SEPARATOR=${SPACE}    ${BY_RTE_FAILURE_PRE}
    ...    RTE IP:    ${UNIT_00_RTE_IP}    ${BY_RTE_FAILURE_POST}
    Should Match    ${checkout_result.stderr}    ${expected}

Check Out By RTE Negative failing on Sonoff IP
    [Documentation]    Should fail due to Sonoff IP non-exclusivity
    ${checkout_result}=    Check Out    rte_ip=${UNIT_02_RTE_IP}

    ${expected}=    Catenate    SEPARATOR=${SPACE}    ${BY_RTE_FAILURE_PRE}
    ...    Sonoff IP:    ${UNIT_02_SONOFF_IP}    ${BY_RTE_FAILURE_POST}

    Should Match    ${checkout_result.stderr}    ${expected}

Check Out By ID Negative failing on PiKVM IP
    [Documentation]    Should fail due to PiKVM IP non-exclusivity
    ${checkout_result}=    Check Out By Asset ID    asset_id=${UNIT_01_ID}

    ${expected}=    Catenate    SEPARATOR=${SPACE}    ${BY_RTE_FAILURE_PRE}
    ...    PiKVM IP:    ${UNIT_02_PIKVM_IP}    ${BY_RTE_FAILURE_POST}

    Should Match    ${checkout_result.stderr}    ${expected}

Check Out By ID Negative failing on Sonoff IP
    [Documentation]    Should fail due to Sonoff IP non-exclusivity
    ${checkout_result}=    Check Out By Asset ID    asset_id=${UNIT_03_ID}

    ${expected}=    Catenate    SEPARATOR=${SPACE}    ${BY_RTE_FAILURE_PRE}
    ...    Sonoff IP:    ${UNIT_03_SONOFF_IP}    ${BY_RTE_FAILURE_POST}

    Should Match    ${checkout_result.stderr}    ${expected}

Flash Probe Negative by RTE IP failing on RTE IP
    [Documentation]    Should fail due to RTE IP non-exclusivity
    ${probe_result}=    Run Process    osfv_cli    rte    --rte_ip
    ...    ${UNIT_00_RTE_IP}    flash    probe
    Should Be Equal As Integers    ${probe_result.rc}    1
    ${expected}=    Catenate    SEPARATOR=${SPACE}    ${BY_RTE_FAILURE_PRE}
    ...    RTE IP:    ${UNIT_00_RTE_IP}    ${BY_RTE_FAILURE_POST}

    Should Match    ${probe_result.stderr}    ${expected}

Flash Probe Negative by RTE IP failing on Sonoff IP
    ${probe_result}=    Run Process    osfv_cli    rte    --rte_ip
    ...    ${UNIT_02_RTE_IP}    flash    probe
    Should Be Equal As Integers    ${probe_result.rc}    1
    ${expected}=    Catenate    SEPARATOR=${SPACE}    ${BY_RTE_FAILURE_PRE}
    ...    Sonoff IP:    ${UNIT_02_SONOFF_IP}    ${BY_RTE_FAILURE_POST}

    Should Match    ${probe_result.stderr}    ${expected}

Sonoff Get Negative by Sonoff IP failing on PiKVM IP
    [Documentation]    Should fail due to PiKVM IP non-exclusivity
    ${probe_result}=    Run Process    osfv_cli    sonoff    --sonoff_ip
    ...    ${UNIT_01_SONOFF_IP}    get
    Should Be Equal As Integers    ${probe_result.rc}    1
    ${expected}=    Catenate    SEPARATOR=${SPACE}    ${BY_RTE_FAILURE_PRE}
    ...    PiKVM IP:    ${UNIT_01_PIKVM_IP}    ${BY_RTE_FAILURE_POST}

    Should Match    ${probe_result.stderr}    ${expected}

Snoff Get Negative by RTE IP failing on Sonoff IP
    [Documentation]    Should fail due to PiKVM IP non-exclusivity
    ${probe_result}=    Run Process    osfv_cli    sonoff    --rte_ip
    ...    ${UNIT_02_RTE_IP}    get
    Should Be Equal As Integers    ${probe_result.rc}    1
    ${expected}=    Catenate    SEPARATOR=${SPACE}    ${BY_RTE_FAILURE_PRE}
    ...    Sonoff IP:    ${UNIT_02_SONOFF_IP}    ${BY_RTE_FAILURE_POST}

    Should Match    ${probe_result.stderr}    ${expected}

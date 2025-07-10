*** Settings ***
Documentation       The goal of this suite is to evaluate the most important features
...                 of the "rte" command, and the "rte.py" library as a consequence as
...                 well. We have a wide variety of hardware platforms in the lab,
...                 which are connected in various ways, with various programmers.
...                 This suite ensures that at least one platform from each type
...                 of setup can be evaluated before proceeding with another release
...                 of the osfv-scripts.

Library             OperatingSystem
Library             Process
Resource            ../test/common/keywords.robot

Suite Setup         Run Keyword    Check In Test Devices


*** Variables ***
${MECHECK_NO_ME_URL}=       https://dl.3mdeb.com/open-source-firmware/Dasharo/protectli_vault_glk/v1.1.1/protectli_vp2410_v1.1.1.rom
${MECHECK_ME_URL}=          https://dl.3mdeb.com/open-source-firmware/Dasharo/protectli_vault_adl/uefi/v0.9.2/protectli_vp66xx_v0.9.2.rom


*** Test Cases ***
Test Flash Probe On RTE v1.0.0 + relay
    [Documentation]    Check if flash on APU2 can be probed. This covers a case
    ...    with v1.0.0 revision of RTE hardware, where SPI lines
    ...    cannot be controlled.
    Run Flash Probe    ${RTE_IP_APU2}

Test Flash Probe On RTE v1.1.0 + relay
    [Documentation]    Check if flash on APU2 can be probed. This covers a case
    ...    with v1.1.0 revision of RTE hardware, where SPI lines
    ...    can be controlled, and relay is used for power control.
    Run Flash Probe    ${RTE_IP_VP4630}

Test Flash Probe On RTE v1.1.0 + Sonoff
    [Documentation]    Check if flash on MSI Z690 can be probed. This covers
    ...    a case with v1.1.0 revision of RTE hardware, where SPI
    ...    lines can be controlled, and Sonoff is used for power
    ...    control.
    Run Flash Probe    ${RTE_IP_Z690}

Test Flash Probe On RTE with CH341A programmer
    [Documentation]    Check if flash on APU2 can be probed. This covers a case
    ...    with CH341 as a programmer, instead of RTE.
    Run Flash Probe    ${RTE_IP_V1410}

Test Flash Probe - Asset Checked Out Manually
    [Documentation]    If we have checked out the device manually before using
    ...    osfv_cli, the device should remain checked out on us,
    ...    not checked in after the script finishes execution.
    Check Out    ${RTE_IP_APU2}
    ${probe_result}=    Run Flash Probe    ${RTE_IP_APU2}
    Should Match
    ...    ${probe_result.stdout}
    ...    *Since the asset ${ASSET_ID_APU2} has been checkout manually by you prior running this script, it will NOT be checked in automatically.*
    Should Match
    ...    ${probe_result.stdout}
    ...    *Please return the device when work is finished.*
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_APU2}*

Test Flash Probe - Asset Checked Out Automatically
    [Documentation]    If we have not checked out the device manually before using
    ...    osfv_cli, the it should be automaticlaly checked out for
    ...    the duration of the script, and checked in once the script
    ...    finishes execution.
    Check In    ${RTE_IP_APU2}
    ${probe_result}=    Run Flash Probe    ${RTE_IP_APU2}
    Should Match
    ...    ${probe_result.stdout}
    ...    *Since the asset ${ASSET_ID_APU2} has been checkout automatically by this script, it is automatically checked in as well.*
    Should Match    ${probe_result.stdout}    *Asset ${ASSET_ID_APU2} successfully checked in.*
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Not Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_APU2}*

Test Flash Probe - Asset Checked Out By Someone Else
    [Documentation]    If the assed has been checked out by someone else, the script
    ...    should stop execution to prevent hardware conflict.
    Check In    ${RTE_IP_APU2}
    # Check out device to robot user
    ${checkout_result}=    Check Out    ${RTE_IP_APU2}    snipeit_config=%{HOME}/.osfv-robot/snipeit.yml
    Should Match    ${checkout_result.stdout}    Asset ${ASSET_ID_APU2} successfully checked out*
    ${list_result}=    Run Process
    ...    osfv_cli
    ...    snipeit
    ...    list_my
    ...    env:SNIPEIT_CONFIG_FILE_PATH=%{HOME}/.osfv-robot/snipeit.yml
    Should Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_APU2}*

    # Probing should fail
    ${probe_result}=    Run Process    osfv_cli    rte    --rte_ip    ${RTE_IP_APU2}    flash    probe
    Should Match    ${probe_result.stdout}    *Error checking out asset ${ASSET_ID_APU2}*
    Should Match
    ...    ${probe_result.stderr}
    ...    *Exiting to avoid conflict. Check who is working on this device and contact them first.*

    # Device should not be checked out on me
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Not Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_APU2}*

    # Device should be checked out on the original owner
    ${list_result}=    Run Process
    ...    osfv_cli
    ...    snipeit
    ...    list_my
    ...    env:SNIPEIT_CONFIG_FILE_PATH=%{HOME}/.osfv-robot/snipeit.yml
    Should Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_APU2}*

Test Flash Check - No ME in image
    [Documentation]    Check image containing descriptor but no ME region
    Check Out    ${RTE_IP_VP2420}
    ${cli_check_out}=    Download And Check Flash Image    ${RTE_IP_VP2420}
    ...    ${MECHECK_NO_ME_URL}
    Should Contain    ${cli_check_out}    FATAL: mecheck.py failed.
    Check In    ${RTE_IP_VP2420}

Test Flash Check - Complete image
    [Documentation]    Check image containing descriptor and ME region
    Check Out    ${RTE_IP_VP2420}
    ${cli_check_out}=    Download And Check Flash Image    ${RTE_IP_VP2420}
    ...    ${MECHECK_ME_URL}
    Should Not Contain    ${cli_check_out}    FATAL: mecheck.py failed.
    Check In    ${RTE_IP_VP2420}

Test Flash Check - No ME in image but DRY check
    [Documentation]    Check image containing descriptor but no ME region
    ...    in dry mode.
    Check Out    ${RTE_IP_VP2420}
    ${cli_check_out}=    Download And Check Flash Image    ${RTE_IP_VP2420}
    ...    ${MECHECK_NO_ME_URL}
    ...    ${TRUE}
    Should Not Contain    ${cli_check_out}    FATAL: mecheck.py failed.
    Check In    ${RTE_IP_VP2420}

Test Flash Check - Complete image but DRY check
    [Documentation]    Check image containing descriptor and ME region in
    ...    dry mode.
    Check Out    ${RTE_IP_VP2420}
    ${cli_check_out}=    Download And Check Flash Image    ${RTE_IP_VP2420}
    ...    ${MECHECK_ME_URL}
    ...    ${TRUE}
    Should Not Contain    ${cli_check_out}    FATAL: mecheck.py failed.
    Check In    ${RTE_IP_VP2420}

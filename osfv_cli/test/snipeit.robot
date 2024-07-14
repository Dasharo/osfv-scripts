*** Settings ***
Documentation       The goal of this suite is to evaluate the most important features
...                 of the "snipeit" command, and the "snipeit.py" library as a consequence as
...                 well.

Library             Process
Resource            ../test/common/keywords.robot

Test Setup          Run Keyword    Check In Test Device
Test Teardown       Run Keyword    Check In Test Device


*** Variables ***
${RTE_IP_TEST_DEVICE}=      ${RTE_IP_FW4C}
${ASSET_ID_TEST_DEVICE}=    ${ASSET_ID_FW4C}


*** Test Cases ***
Check Out Unused Device
    [Documentation]    If device was unused, check out should be successful.
    ${checkout_result}=    Check Out    ${RTE_IP_TEST_DEVICE}
    Should Match    ${checkout_result.stdout}    Asset ${ASSET_ID_TEST_DEVICE} successfully checked out*
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_TEST_DEVICE}*

Check Out Used Device (by me)
    [Documentation]    If device was already checked out by me, it should stay
    ...    checked out this way. No error should be returned.
    ${checkout_result}=    Check Out    ${RTE_IP_TEST_DEVICE}
    Should Match    ${checkout_result.stdout}    Asset ${ASSET_ID_TEST_DEVICE} successfully checked out*
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_TEST_DEVICE}*

Check Out Used Device (by someone else)
    [Documentation]    If device was already checked out by someone else, it
    ...    should stay checked out this way. An error should be
    ...    returned that devices is already used by someone else.
    # Check out device to robot user
    ${checkout_result}=    Check Out    ${RTE_IP_TEST_DEVICE}    snipeit_config=%{HOME}/.osfv-robot/snipeit.yml
    Should Match    ${checkout_result.stdout}    Asset ${ASSET_ID_TEST_DEVICE} successfully checked out*
    ${list_result}=    Run Process
    ...    osfv_cli
    ...    snipeit
    ...    list_my
    ...    env:SNIPEIT_CONFIG_FILE_PATH=%{HOME}/.osfv-robot/snipeit.yml
    Should Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_TEST_DEVICE}*

    # Try to check out already used device
    ${checkout_result}=    Check Out    ${RTE_IP_TEST_DEVICE}
    Should Match    ${checkout_result.stdout}    *Error checking out asset ${ASSET_ID_TEST_DEVICE}*
    Should Match    ${checkout_result.stdout}    *That asset is not available for checkout!*

Check In Unused Device
    [Documentation]    If device was unused, we should be informed that there is
    ...    no need to check in, as the device is not used.
    ${checkin_result}=    Check In    ${RTE_IP_TEST_DEVICE}
    Should Match    ${checkin_result.stdout}    *Error checking in asset ${ASSET_ID_TEST_DEVICE}*
    Should Match    ${checkin_result.stdout}    *hat asset is already checked in.*
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Not Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_TEST_DEVICE}*

Check In Used Device (by me)
    [Documentation]    If device was used by me, check in should be successful.
    # Check out device
    ${checkout_result}=    Check Out    ${RTE_IP_TEST_DEVICE}
    Should Match    ${checkout_result.stdout}    Asset ${ASSET_ID_TEST_DEVICE} successfully checked out*
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_TEST_DEVICE}*

    # Check in device
    ${checkin_result}=    Check In    ${RTE_IP_TEST_DEVICE}
    Should Match    ${checkin_result.stdout}    Asset ${ASSET_ID_TEST_DEVICE} successfully checked in*
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Not Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_TEST_DEVICE}*

Check In Used Device (by someone else)
    [Documentation]    If device was used by someone else, check in should fail.
    ...    An error should be returned that the device is already
    ...    used bye someone else.
    # Check out device to robot user
    ${checkout_result}=    Check Out    ${RTE_IP_TEST_DEVICE}    snipeit_config=%{HOME}/.osfv-robot/snipeit.yml
    Should Match    ${checkout_result.stdout}    Asset ${ASSET_ID_TEST_DEVICE} successfully checked out*
    ${list_result}=    Run Process
    ...    osfv_cli
    ...    snipeit
    ...    list_my
    ...    env:SNIPEIT_CONFIG_FILE_PATH=%{HOME}/.osfv-robot/snipeit.yml
    Should Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_TEST_DEVICE}*

    # Check in device as me - should fail (?)
    ${checkin_result}=    Check In    ${RTE_IP_TEST_DEVICE}
    Should Match    ${checkin_result.stdout}    Asset ${ASSET_ID_TEST_DEVICE} successfully checked in*
    ${list_result}=    Run Process    osfv_cli    snipeit    list_my
    Should Not Match    ${list_result.stdout}    *Asset ID: ${ASSET_ID_TEST_DEVICE}*


*** Keywords ***
Check In Test Device
    [Documentation]    Make sure that at the start of each case, device is
    ...    checked in by both users.
    Check In    ${RTE_IP_TEST_DEVICE}
    Check In    ${RTE_IP_TEST_DEVICE}    snipeit_config=%{HOME}/.osfv-robot/snipeit.yml

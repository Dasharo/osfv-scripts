*** Settings ***
Documentation       The goal of this suite is to test flash_image_check command.

Library             OperatingSystem
Library             Process
Resource            ../test/common/keywords.robot

Suite Setup         Run Keyword    Check In Test Devices


*** Variables ***
${MECHECK_NO_ME_URL}=                   https://dl.3mdeb.com/open-source-firmware/Dasharo/protectli_vault_glk/v1.1.1/protectli_vp2410_v1.1.1.rom
${MECHECK_ME_URL}=                      https://dl.3mdeb.com/open-source-firmware/Dasharo/protectli_vault_adl/uefi/v0.9.2/protectli_vp66xx_v0.9.2.rom
${EXPECTED_STDERR_FAILURE_STRING}=      Do not flash full image, unless you are skipping empty regions, and know what you are doing!
${EXPECTED_STDOUT_SUCCESS_STRING}=      SUCCESS: region "me" is present and contains some data.


*** Test Cases ***
Test Flash Check - No ME in image
    [Documentation]    Check image containing descriptor but no ME region
    ${cli_check_out}=    Download And Check Flash Image
    ...    ${MECHECK_NO_ME_URL}
    Should Contain    ${cli_check_out.stderr}    ${EXPECTED_STDERR_FAILURE_STRING}

Test Flash Check - Complete image
    [Documentation]    Check image containing descriptor and ME region
    ${cli_check_out}=    Download And Check Flash Image
    ...    ${MECHECK_ME_URL}
    Should Not Contain    ${cli_check_out.stderr}    flash_image_check failed.
    Should Contain    ${cli_check_out.stdout}    ${EXPECTED_STDOUT_SUCCESS_STRING}

Test Flash Check - No ME in image but DRY check
    [Documentation]    Check image containing descriptor but no ME region
    ...    in dry mode.
    ${cli_check_out}=    Download And Check Flash Image
    ...    ${MECHECK_NO_ME_URL}
    ...    ${TRUE}
    Should Not Contain    ${cli_check_out.stderr}    ${EXPECTED_STDERR_FAILURE_STRING}

Test Flash Check - Complete image but DRY check
    [Documentation]    Check image containing descriptor and ME region in
    ...    dry mode.
    ${cli_check_out}=    Download And Check Flash Image
    ...    ${MECHECK_ME_URL}
    ...    ${TRUE}
    Should Not Contain    ${cli_check_out.stderr}    ${EXPECTED_STDERR_FAILURE_STRING}
    Should Contain    ${cli_check_out.stdout}    ${EXPECTED_STDOUT_SUCCESS_STRING}

*** Settings ***
Documentation       The goal of this suite is to stress test SnipeIT API

Library             Collections
Library             Process
Resource            ../test/common/keywords.robot


*** Test Cases ***
Call SnipeIT API 10 Times Sequentially
    [Documentation]    This is expected to PASS rliably at all times
    FOR    ${i}    IN RANGE    10
        Log    Run number: ${i}
        ${result}=    Run Process    osfv_cli    snipeit    list_my
        Log    ${result.stdout}
        Log    ${result.stderr}
        Should Be Empty    ${result.stderr}
    END

Run OSFV CLI 40 Times In Parallel
    [Documentation]    This was expected to fail prior implementing more resilient requests handling.

    ${handles}=    Create List
    FOR    ${i}    IN RANGE    50
        ${handle}=    Start Process    osfv_cli    snipeit    list_my    shell=True
        Append To List    ${handles}    ${handle}
    END
    ${index}=    Set Variable    0
    FOR    ${handle}    IN    @{handles}
        ${result}=    Wait For Process    ${handle}    timeout=30
        Log    STDOUT ${index}: ${result.stdout}
        Log    STDERR ${index}: ${result.stderr}
        ${index}=    Evaluate    ${index} + 1
        Should Be Empty    ${result.stderr}
    END

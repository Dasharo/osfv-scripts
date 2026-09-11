*** Settings ***
Documentation       lib/models.py (Models class) test suite

Library             OperatingSystem
Library             Process
Library             String

Suite Setup         Create Test Venv
Suite Teardown      Remove Directory    ${VENV}    recursive=True


*** Variables ***
${VENV}     ${TEMPDIR}/osfv-cli-test-venv


*** Test Cases ***
Correct model .yml
    OperatingSystem.Copy File    ./test/data/FakeDevice.yml    ./src/osfv/models/

    Install Osfv Cli

    ${result}=    Run Osfv Cli    list_models
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeDevice*VERIFIED
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeDevice.yml

SPI mux model .yml
    [Documentation]    A model on an RTE with the SPI mux extension, which lists
    ...    each flash and the SPI header it is wired to.
    OperatingSystem.Copy File    ./test/data/FakeSPIMux.yml    ./src/osfv/models/

    Install Osfv Cli

    ${result}=    Run Osfv Cli    list_models
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeSPIMux*VERIFIED
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeSPIMux.yml

Model .yml with no flash chip
    [Documentation]    An empty flash_chip list satisfies "a list of flash chips"
    ...    with nothing in it to check, so it has to be rejected on its own.
    OperatingSystem.Copy File    ./test/data/FakeDeviceNoFlash.yml    ./src/osfv/models/

    Install Osfv Cli

    ${result}=    Run Osfv Cli    list_models
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeDeviceNoFlash*INCOMPLETE
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeDeviceNoFlash.yml

Broken model .yml
    OperatingSystem.Copy File    ./test/data/FakeDeviceBroken.yml    ./src/osfv/models/

    Install Osfv Cli

    ${result}=    Run Osfv Cli    list_models
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeDeviceBroken*INCOMPLETE
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeDeviceBroken.yml


*** Keywords ***
Create Test Venv
    [Documentation]    Creates the virtual environment the suite installs into.
    ${result}=    Run Process    uv    venv    ${VENV}
    Should Be Equal As Integers    ${result.rc}    0    ${result.stderr}

Install Osfv Cli
    [Documentation]    Installs the package into the suite virtual environment.
    ...
    ...    The install is a regular one, so a model file reaches the command
    ...    only by being packaged, which is what these tests check. Keeping it
    ...    in a virtual environment of its own leaves the installation on the
    ...    host alone.
    ${result}=    Run Process    uv    pip    install    --python    ${VENV}    .
    Should Be Equal As Integers    ${result.rc}    0    ${result.stderr}

Run Osfv Cli
    [Documentation]    Runs `osfv_cli` from the suite virtual environment.
    [Arguments]    @{args}
    ${result}=    Run Process    ${VENV}/bin/osfv_cli    @{args}
    RETURN    ${result}

*** Settings ***
Documentation       lib/models.py (Models class) test suite

Library             OperatingSystem
Library             Process
Library             String


*** Test Cases ***
Correct model .yml
    OperatingSystem.Copy File    ./test/data/FakeDevice.yml    ./src/osfv/models/

    Run Process    make    install

    ${result}=    Run Process    osfv_cli    list_models    stdout=True
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeDevice*VERIFIED
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeDevice.yml

SPI mux model .yml
    [Documentation]    A model on an RTE with the SPI mux extension, which lists
    ...    each flash and the SPI header it is wired to.
    OperatingSystem.Copy File    ./test/data/FakeSPIMux.yml    ./src/osfv/models/

    Run Process    make    install

    ${result}=    Run Process    osfv_cli    list_models    stdout=True
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeSPIMux*VERIFIED
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeSPIMux.yml

Model .yml with no flash chip
    [Documentation]    An empty flash_chip list satisfies "a list of flash chips"
    ...    with nothing in it to check, so it has to be rejected on its own.
    OperatingSystem.Copy File    ./test/data/FakeDeviceNoFlash.yml    ./src/osfv/models/

    Run Process    make    install

    ${result}=    Run Process    osfv_cli    list_models    stdout=True
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeDeviceNoFlash*INCOMPLETE
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeDeviceNoFlash.yml

Broken model .yml
    OperatingSystem.Copy File    ./test/data/FakeDeviceBroken.yml    ./src/osfv/models/

    Run Process    make    install

    ${result}=    Run Process    osfv_cli    list_models    stdout=True
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeDeviceBroken*INCOMPLETE
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeDeviceBroken.yml

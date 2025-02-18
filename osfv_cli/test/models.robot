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

Broken model .yml
    OperatingSystem.Copy File    ./test/data/FakeDeviceBroken.yml    ./src/osfv/models/

    Run Process    make    install

    ${result}=    Run Process    osfv_cli    list_models    stdout=True
    Log    ${result.stdout}

    ${regex_result}=    Get Lines Matching Pattern    ${result.stdout}    FakeDeviceBroken*INCOMPLETE
    Log    ${regex_result}

    Should Not Be Empty    ${regex_result}
    OperatingSystem.Remove File    ./src/osfv/models/FakeDeviceBroken.yml

#!/usr/bin/env python3

import argparse
import json
from copy import copy
from importlib import metadata
from time import sleep

import osfv.libs.utils as utils
import pexpect
import requests
from osfv.libs.models import Models
from osfv.libs.rte import RTE
from osfv.libs.snipeit_api import SnipeIT
from osfv.libs.sonoff_api import SonoffDevice
from osfv.libs.zabbix import Zabbix


def check_out_asset(snipeit_api, asset_id):
    """
    Attempts to check out an asset..
    It checks if the asset is already checked out by the user.

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.
        asset_id (str): The unique identifier of the asset to be checked out.

    Returns:
        None
    """
    success, data, already_checked_out = snipeit_api.check_out_asset(asset_id)

    if already_checked_out:
        print(f"Asset {asset_id} is already checked out by you")
        return already_checked_out

    if success:
        print(f"Asset {asset_id} successfully checked out.")
    else:
        print(f"Error checking out asset {asset_id}")
        print(f"Response data: {data}")
        exit(
            f"Exiting to avoid conflict. Check who is working on this device"
            f" and contact them first."
        )

    return already_checked_out


def check_in_asset(snipeit_api, asset_id):
    """
    Checks in an asset to the system by its asset ID.

    This method attempts to check in the specified asset identified by `asset_id` by making an HTTP POST request.
    If the check-in is successful, it returns a success flag and the JSON response from the API.
    If the check-in fails, it returns a failure flag and the error message from the API.

    Parameters:
    asset_id (str): The unique identifier of the asset to be checked in.

    Returns:
    tuple:
        bool: Indicates if the check-in operation was successful (True) or not (False).
        dict: The JSON response from the API, either containing success information or error details.
    """
    success, data = snipeit_api.check_in_asset(asset_id)

    if success:
        print(f"Asset {asset_id} successfully checked in.")
        return True
    else:
        print(f"Error checking in asset {asset_id}")
        print(f"Response data: {data}")
        return False


def list_used_assets(snipeit_api, args):
    """
    Retrieves and displays all used assets.

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    all_assets = snipeit_api.get_all_assets()
    used_assets = [
        asset for asset in all_assets if asset["assigned_to"] is not None
    ]

    if not used_assets:
        print("No used assets found.")
        return

    if args.json:
        print(json.dumps(used_assets))
    else:
        for asset in used_assets:
            print_asset_details(asset)


def get_my_assets(snipeit_api):
    """
    Gets a list of assets assigned to the current user

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.

    Returns:
        List of assets assigned to the current user
    """
    all_assets = snipeit_api.get_all_assets()
    used_assets = [
        asset for asset in all_assets if asset["assigned_to"] is not None
    ]
    return [
        asset
        for asset in used_assets
        if asset["assigned_to"]["id"] is snipeit_api.cfg_user_id
    ]


def list_my_assets(snipeit_api, args):
    """
    Lists all assets assigned to the current user.

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        Boolean: False if no assets were assigned to the user, True otherwise
    """
    my_assets = get_my_assets(snipeit_api)

    if not my_assets:
        print("No used assets found.")
        return False

    if args.json:
        print(json.dumps(my_assets))
    else:
        for asset in my_assets:
            print_asset_details(asset)
    return True


def check_in_my(snipeit_api, args):
    """
    Lists all assets assigned to the current user, checks in all of them
    except those which are in a category listed in `categories_to_ignore`.

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.
        args (object): Arguments that may contain additional parameters
        (not used in this function).

    Returns:
        None
    """
    categories_to_ignore = ["Employee Laptop"]
    my_assets = get_my_assets(snipeit_api)

    my_assets = [
        asset
        for asset in my_assets
        if not set(asset["category"].values()) & set(categories_to_ignore)
    ]
    if not list_my_assets(snipeit_api, args):
        return

    if not args.yes:
        print(
            f"Are you sure you want to check in {len(my_assets)} assets? [y/N]"
        )
        if input() != "y":
            print(f"Checking in {len(my_assets)} assets aborted.")
            return

    failed = []
    for asset in my_assets:
        if not check_in_asset(snipeit_api, asset["id"]):
            failed = failed.append(asset)

    if failed:
        print(f"Failed to check-in {len(failed)} assets:")
    else:
        print(f"{len(my_assets)} assets checked in successfully.")


def list_unused_assets(snipeit_api, args):
    """
    Retrieves all assets.

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    all_assets = snipeit_api.get_all_assets()
    unused_assets = [
        asset for asset in all_assets if asset["assigned_to"] is None
    ]

    if not unused_assets:
        print("No unused assets found.")
        return

    if args.json:
        print(json.dumps(unused_assets))
    else:
        for asset in unused_assets:
            print_asset_details(asset)


def list_all_assets(snipeit_api, args):
    """
    Retrieves all assets using.

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    all_assets = snipeit_api.get_all_assets()

    if not all_assets:
        print("No assets found.")
        return

    if args.json:
        print(json.dumps(all_assets))
    else:
        for asset in all_assets:
            print_asset_details(asset)


def list_for_zabbix(snipeit_api, args):
    """
    Print asset details as JSON with specific custom fields.

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    all_assets = snipeit_api.get_all_assets()

    if all_assets:
        for asset in all_assets:
            print_asset_details_for_zabbix(asset)
    else:
        print("No assets found.")


def print_asset_details(asset):
    """
    Prints details of a given asset, including its basic information, assigned user (if any),
    and custom fields.

    Args:
        asset (dict): Dictionary containing asset details.

    Returns:
        None
    """

    print(
        f'Asset Tag: {asset["asset_tag"]}, Asset ID: {asset["id"]},'
        f'Name: {asset["name"]}, Serial: {asset["serial"]}'
    )

    if asset["assigned_to"]:
        print(f'Assigned to: {asset["assigned_to"]["name"]}')

    custom_fields = asset.get("custom_fields", {})
    if custom_fields:
        for field_name, field_data in custom_fields.items():
            field_value = field_data.get("value")
            print(f"{field_name}: {field_value}")

    print()


def get_zabbix_compatible_assets_from_asset(asset):
    """
    Extracts an asset to zabbix assets.

    Args:
        asset (dict): Dictionary containing asset details.

    Returns:
        The dictionary with asset tags as keys and asset data as value.
    """
    result = {}
    custom_fields = asset.get("custom_fields", {})
    if custom_fields:
        for field_name, field_data in custom_fields.items():
            if field_name in ["RTE IP", "Sonoff IP", "PiKVM IP"]:
                field_value = field_data.get("value")
                if field_value:
                    key = f'{asset["asset_tag"]}_{field_name}'.replace(
                        " ", "_"
                    )
                    result[key] = field_value
    return result


def print_asset_details_for_zabbix(asset):
    """
    Print asset details formatted as an input for Zabbix import script.

    Args:
        asset (dict): Dictionary containing asset details.

    Returns:
        None.
    """
    assets = get_zabbix_compatible_assets_from_asset(asset)
    for key in assets.keys():
        print(f"{key}: {assets[key]}")


def relay_toggle(rte, args):
    """
    Toggle the state of a relay controlled by the rte object.

    Args:
        rte: An object responsible for controlling the relay.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None.
    """
    state_str = rte.relay_get()
    if state_str == RTE.PSU_STATE_OFF:
        new_state_str = RTE.PSU_STATE_ON
    else:
        new_state_str = RTE.PSU_STATE_OFF
    rte.relay_set(new_state_str)
    state = rte.relay_get()
    print(f"Relay state toggled. New state: {state}")


def relay_set(rte, args):
    """
    Sets the relay state based on the provided args.state value.

    Args:
        rte: An object responsible for controlling the relay.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None.
    """
    rte.relay_set(args.state)
    state = rte.relay_get()
    print(f"Relay state set to {state}")


def relay_get(rte, args):
    """
    Get the state of the relay and print it.

    Args:
        rte (object): The object representing the relay control interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    state = rte.relay_get()
    print(f"Relay state: {state}")


def power_on(rte, args):
    """
    Power on the DUT if the power supply is enabled.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    state = rte.psu_get()
    if state != rte.PSU_STATE_ON:
        print(f"Power supply state: {state} !")
        print(
            "If you wanted to power on the DUT, you need to enable power suppl"
            'y first ("pwr psu on"), pushing the power button is not enough!'
        )
    print(f"Powering on...")
    rte.power_on(args.time)


def power_off(rte, args):
    """
    Power off the DUT.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    print(f"Powering off...")
    rte.power_off(args.time)


def power_on_ex(rte, args):
    power_on(rte, args)
    for attempt in range(20):
        if check_pwr_led(rte, args) == "high":
            print("Power on successful.")
            return True
        sleep(0.25)
    print("Power on failed.")
    return False


def power_off_ex(rte, args):
    power_off(rte, args)
    for attempt in range(20):
        if check_pwr_led(rte, args) == "low":
            print("Power off successful.")
            return True
        sleep(0.25)
    print("Power off failed.")
    return False


def reset(rte, args):
    """
    Reset the DUT by pressing the reset button.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    print(f"Pressing reset button...")
    rte.reset(args.time)


def psu_on(rte, args):
    """
    Enable the power supply to the DUT.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    print(f"Enabling power supply...")
    rte.psu_on()


def psu_off(rte, args):
    """
    Disable the power supply to the DUT.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    print(f"Disabling power supply...")
    rte.psu_off()


def psu_get(rte, args):
    """
    Retrieve and print the current power supply state.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    state = rte.psu_get()
    print(f"Power supply state: {state}")


def gpio_get(rte, args):
    """
    Retrieve and print the state of a specified GPIO pin.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    state = rte.gpio_get(args.gpio_no)
    print(f"GPIO {args.gpio_no} state: {state}")


def check_pwr_led(rte, args):
    state = rte.gpio_get(RTE.GPIO_PWR_LED)
    polarity = rte.dut_data.get("pwr_led", {}).get("polarity")
    if polarity and polarity == "active low":
        if state == "high":
            state = "low"
        else:
            state = "high"

    print(f"Power LED state: {'ON' if state == 'high' else 'OFF'}")
    return state


def gpio_set(rte, args):
    """
    Set the state of a specified GPIO pin and print the new state.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    rte.gpio_set(args.gpio_no, args.state)
    state = rte.gpio_get(args.gpio_no)
    print(f"GPIO {args.gpio_no} state set to {state}")


def gpio_list(rte, args):
    """
    Retrieve and print the list of available GPIO pins.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    response = json.dumps(rte.gpio_list(), indent=4)
    print(f"GPIO list")
    print(response)


def rte_status(rte, args):
    """
    Set the state of a GPIO pin and print its new state.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    rte.gpio_set(args.gpio_no, args.state)
    state = rte.gpio_get(args.gpio_no)
    print(f"GPIO {args.gpio_no} state set to {state}")


def open_dut_serial(rte, args):
    """
    Open a Telnet session to interact with the DUT serial interface.

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    host = args.rte_ip
    port = 13541

    print(f"Opening telnet session with: {host}:{port}")
    print(f"Press Ctrl+] to exit")
    # Connect to the Telnet server
    tn = pexpect.spawn(f"telnet {host} {port}")

    # Enter the interactive shell
    tn.interact()


def spi_on(rte, args):
    """
    Enable SPI on the Device Under Test (DUT).

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    print(f"Enabling SPI...")
    rte.spi_enable()


def spi_off(rte, args):
    """
    Disable SPI on the Device Under Test (DUT).

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    print(f"Disabling SPI...")
    rte.spi_disable()


def flash_probe(rte, args):
    """
    Probe the flash memory on the Device Under Test (DUT).

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    print(f"Probing flash...")
    rte.flash_probe()


def flash_read(rte, args):
    """
    Read the flash content from the Device Under Test (DUT).

    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None
    """
    print(f"Reading from flash...")
    rte.flash_read(args.rom)
    print(f"Read flash content saved to {args.rom}")


def flash_write(rte, args):
    """
    Write a specified ROM file to the flash memory using the rte object.

    Args:
        rte: An object responsible for handling the flash memory operations.
        args (object): Arguments that may contain additional parameters:
        args.rom (str): Flash image file path & name
        args.dry_mecheck (bool): runs ME check in dry run mode;
                                 check status is always positive and does not
                                 affect flash write process
        args.verbosity (bool): increases osfv.libs.flash_image verbosity


    Returns:
        None.
    """
    if (
        utils.check_flash_image_regions(
            args.rom, args.dry_mecheck, args.verbosity
        )
        == False
    ):
        exit(
            "FATAL: Image could not be loaded, or some image's regions are empty, despite being defined in the flash descriptor. "
            "Flashing full image in this form on Intel platform will result in a bricked platform. "
            "If you wish to continue anyway (e.g. when using AMD platform), pass the -x option to skip the check. "
            "When using Intel platform, you probably also want to pass the -b option to flash BIOS region only, "
            "leaving other regions in platform's flash (such as ME) intact."
        )
    print(f"Writing {args.rom} to flash...")
    rc = rte.flash_write(args.rom, args.bios)
    if rc == 0:
        print(f"Flash written successfully")
    else:
        print(f"Flash write failed with code {rc}")


def flash_erase(rte, args):
    """
    Erases the flash memory of the device under test (DUT) using the rte object.

    Args:
        rte: The object used to interact with the device, which includes methods for flash operations.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None.
    """
    print(f"Erasing DUT flash...")
    rte.flash_erase()
    print(f"Flash erased")


def sonoff_on(sonoff, args):
    """
    Attempts to turn on the Sonoff power switch and prints the response.

    Args:
        sonoff: An object responsible for controlling the Sonoff power switch.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None.
    """
    print("Turning on Sonoff power switch...")
    try:
        response = sonoff.turn_on()
        print(response)
    except requests.exceptions.RequestException as e:
        print(f"Failed to turn on Sonoff power switch. Error: {e}")


def sonoff_off(sonoff, args):
    """
    Attempts to turn off the Sonoff power switch and prints the response.

    Args:
        sonoff: An object responsible for controlling the Sonoff power switch.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None.
    """
    print("Turning off Sonoff power switch...")
    try:
        response = sonoff.turn_off()
        print(response)
    except requests.exceptions.RequestException as e:
        print(f"Failed to turn off Sonoff power switch. Error: {e}")


def sonoff_get(sonoff, args):
    """
    Retrieves the current state of the Sonoff power switch and prints it.

    Args:
        sonoff: An object responsible for controlling the Sonoff power switch.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None.
    """
    print("Getting Sonoff power switch state...")
    try:
        state = sonoff.get_state()
        print(f"Sonoff power switch state: {state}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to get Sonoff power switch state. Error: {e}")


def sonoff_tgl(sonoff, args):
    """
    Toggles the current state of the Sonoff power switch.

    Args:
        sonoff: An object responsible for controlling the Sonoff power switch.
        args (object): Arguments that may contain additional parameters (not used in this function).

    Returns:
        None.
    """
    print("Toggling Sonoff power switch state...")
    try:
        current_state = sonoff.get_state()

        if current_state == "ON":
            response = sonoff.turn_off()
            print("Sonoff power switch state toggled off.")
        elif current_state == "OFF":
            response = sonoff.turn_on()
            print("Sonoff power switch state toggled on.")
        else:
            print(f"Unexpected Sonoff power switch state: {current_state}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to toggle Sonoff power switch state. Error: {e}")


def ask_to_proceed(message="Do you want to proceed (y/n): "):
    """
    Prompts the user with a yes/no question and returns the user's choice.

    Args:
        message (str, optional): The prompt message to display. Defaults to "Do you want to proceed (y/n): ".

    Returns:
        bool: True if the user enters 'y', False if the user enters 'n'.
    """
    print("")
    while True:
        choice = input(message).lower()
        if choice in ["y", "n"]:
            return choice == "y"
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def update_zabbix_assets(snipeit_api):
    """
    Updates Zabbix with the latest asset data from Snipe-IT, ensuring the IP addresses
    are synchronized between Snipe-IT and Zabbix.

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.

    Returns:
        None.
    """
    zabbix = Zabbix()
    all_assets = snipeit_api.get_all_assets()

    current_zabbix_assets = zabbix.get_all_hosts()
    # snipeit assets but converted to zabbix-form assets
    snipeit_assets = {}

    update_available = False

    if all_assets:
        for asset in all_assets:
            snipeit_assets.update(
                get_zabbix_compatible_assets_from_asset(asset)
            )

    snipeit_assets_keys = list(snipeit_assets.keys())

    snipeit_configuration_error = False

    forbidden_symbols = [
        "/",
        "\\",
        "{",
        "}",
        ";",
        ":",
        "~",
        "`",
        '"',
        "'",
        "[",
        "]",
        "|",
        "<",
        ">",
        "$",
        "#",
        "@",
        "%",
        "^",
        "&",
        "*",
        "(",
        ")",
        "+",
        "=",
    ]

    for i in range(snipeit_assets.__len__()):
        # check for duplicates
        for j in range(i + 1, snipeit_assets.__len__()):
            if (
                snipeit_assets[snipeit_assets_keys[i]]
                == snipeit_assets[snipeit_assets_keys[j]]
            ):
                print(
                    f"{snipeit_assets_keys[i]} has the same IP as "
                    f"{snipeit_assets_keys[j]}!"
                )
                snipeit_configuration_error = True
            if snipeit_assets_keys[i] == snipeit_assets_keys[j]:
                print(
                    f"There are at least 2 assets with name "
                    f"{snipeit_assets_keys[i]} present!"
                )
                snipeit_configuration_error = True

        # check for forbidden symbols in asset names
        if any(
            symbol in snipeit_assets_keys[i] for symbol in forbidden_symbols
        ):
            print(
                f"{snipeit_assets_keys[i]} contains forbidden symbols! They "
                f"are going to be changed to '_'."
            )
            new_key = copy(snipeit_assets_keys[i])
            for s in forbidden_symbols:
                new_key = new_key.replace(s, "_")

            snipeit_assets[new_key] = snipeit_assets.pop(
                snipeit_assets_keys[i]
            )

    if snipeit_configuration_error:
        print(
            "\nSnipeIT configuration errors have been detected! "
            "Fix them and then continue."
        )
        return

    keys_not_present_in_zabbix = set(snipeit_assets.keys()) - set(
        current_zabbix_assets.keys()
    )

    keys_not_present_in_snipeit = set(current_zabbix_assets.keys()) - set(
        snipeit_assets.keys()
    )

    if (
        keys_not_present_in_zabbix.__len__() > 0
        or keys_not_present_in_snipeit.__len__() > 0
    ):
        update_available = True

    common_keys = set(snipeit_assets.keys()) & set(
        current_zabbix_assets.keys()
    )

    if keys_not_present_in_zabbix.__len__() > 0:
        print("Assets not present in Zabbix (these will be added):")
        print("\n".join(keys_not_present_in_zabbix))

    if keys_not_present_in_snipeit.__len__() > 0:
        print(
            "\nAssets present in Zabbix but not in SnipeIT "
            "(these will be removed):"
        )
        print("\n".join(keys_not_present_in_snipeit))

    print("")
    keys_for_ip_change = []
    for key in common_keys:
        if snipeit_assets[key] != current_zabbix_assets[key]:
            print(
                f"{key} has wrong IP! (Zabbix one will be updated from "
                f"{current_zabbix_assets[key]} to {snipeit_assets[key]})"
            )
            keys_for_ip_change.append(key)

    if keys_for_ip_change.__len__() > 0:
        update_available = True

    if not update_available:
        print("Zabbix is already synced with SnipeIT")
        return

    if not ask_to_proceed("Do you want to apply above changes? (y/n): "):
        print("Changes were not applied")
        return

    # removing zabbix hosts
    for key in keys_not_present_in_snipeit:
        print(f"Removing {key}({current_zabbix_assets[key]})...")
        result = zabbix.remove_host_by_name(key)
        if "error" in result:
            print("Failed to remove the host!")

    # updating zabbix ips
    for key in keys_for_ip_change:
        print(f"Updating {key} IP to {snipeit_assets[key]}...")
        result = zabbix.update_host_ip(key, snipeit_assets[key])
        if "error" in result:
            print("Failed to change host's IP!")

    # adding zabbix hosts
    for key in keys_not_present_in_zabbix:
        print(f"Adding {key}({snipeit_assets[key]})...")
        try:
            result = zabbix.add_host(key, snipeit_assets[key])
        except ValueError:
            print("Failed to add the host!")


def list_models(args):
    models = Models()
    models.list_models()


def flash_image_check(args):
    """
    Checks for existence & sane content of ME region in flash image.

    Args:
        args (object): Arguments that may contain additional parameters:
        args.list (bool): List known regions and exit
        args.rom (str): Flash image file path & name
        args.dry_mecheck (bool): runs osfv.libs.flash_image in dry run mode;
                                 exit status is always positive
        args.verbosity (bool): increases osfv.libs.flash_image verbosity
        args.regions_to_check [str]: list of regions to check
        args.regions_to_dump [str]: list of regions to dump to separate files

    Returns:
        None.
    """

    regions_to_check = ["me"]

    if args.list:
        print("Known flash regions:")
        for reg_name in utils.get_list_of_known_image_regions():
            print(reg_name)
        exit()
    if args.regions_to_check:
        regions_to_check = args.regions_to_check
    if args.regions_to_dump:
        utils.dump_flash_image_regions(
            args.rom, args.verbosity, args.regions_to_dump
        )
    if (
        utils.check_flash_image_regions(
            args.rom, args.dry_mecheck, args.verbosity, regions_to_check
        )
        == False
    ):
        exit(
            "Do not flash full image, unless you are skipping empty regions, and know what you are doing!"
        )


def reset_cmos(rte, args):
    """
    Resets the CMOS of the Device Under Test (DUT).
    Args:
        rte (object): The object representing the relay control and power supply interface.
        args (object): Arguments that may contain additional parameters (not used in this function).
    Returns:
        None
    """
    print(f"Clearing CMOS...")
    rte.reset_cmos()


# Main function
def main():
    parser = argparse.ArgumentParser(
        description="Open Source Firmware Validation CLI"
    )
    parser.add_argument(
        "-v", "--version", action="version", version=metadata.version("osfv")
    )

    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Output as JSON (if applicable)",
    )

    subparsers = parser.add_subparsers(
        title="commands", dest="command", help="Command to execute"
    )

    snipeit_parser = subparsers.add_parser("snipeit", help="Snipe-IT commands")

    rte_parser = subparsers.add_parser("rte", help="RTE commands")
    sonoff_parser = subparsers.add_parser("sonoff", help="Sonoff commands")
    list_models_parser = subparsers.add_parser(
        "list_models", help="List of supported models"
    )

    # Sonoff subcommands
    sonoff_group = sonoff_parser.add_mutually_exclusive_group(required=True)
    sonoff_group.add_argument(
        "--sonoff_ip", type=str, help="Sonoff IP address"
    )
    sonoff_group.add_argument("--rte_ip", type=str, help="RTE IP address")
    sonoff_subparsers = sonoff_parser.add_subparsers(
        title="subcommands", dest="sonoff_cmd", help="Sonoff subcommands"
    )

    sonoff_subparsers.add_parser("on", help="Turn Sonoff ON")
    sonoff_subparsers.add_parser("off", help="Turn Sonoff OFF")
    sonoff_subparsers.add_parser("tgl", help="Toggle Sonoff state")
    sonoff_subparsers.add_parser("get", help="Get Sonoff state")

    # Snipe-IT subcommands
    snipeit_subparsers = snipeit_parser.add_subparsers(
        title="subcommands", dest="snipeit_cmd", help="Snipe-IT subcommands"
    )

    list_used_parser = snipeit_subparsers.add_parser(
        "list_used", help="List all already used assets"
    )

    list_my_parser = snipeit_subparsers.add_parser(
        "list_my", help="List all my used assets"
    )

    list_unused_parser = snipeit_subparsers.add_parser(
        "list_unused", help="List all unused assets"
    )

    list_all_parser = snipeit_subparsers.add_parser(
        "list_all", help="List all assets"
    )

    list_zabbix_parser = snipeit_subparsers.add_parser(
        "list_for_zabbix",
        help="List assets in a format suitable for Zabbix integration",
    )

    update_zabbix_assets_parser = snipeit_subparsers.add_parser(
        "update_zabbix",
        help="Syncs Zabbix assets with SnipeIT ones",
    )

    check_out_parser = snipeit_subparsers.add_parser(
        "check_out",
        help="Check out an asset by providing the Asset ID or RTE IP",
    )
    check_out_group = check_out_parser.add_mutually_exclusive_group(
        required=True
    )
    check_out_group.add_argument("--asset_id", type=int, help="Asset ID")
    check_out_group.add_argument("--rte_ip", type=str, help="RTE IP")
    check_out_parser = snipeit_subparsers.add_parser(
        "user_add",
        help="Add a new user by providing user First Name and Last Name",
    )
    check_out_parser.add_argument(
        "--first-name", type=str, help="User First Name", required=True
    )
    check_out_parser.add_argument(
        "--last-name", type=str, help="User Last Name", required=True
    )
    check_out_parser.add_argument(
        "--company-name", type=str, default="3mdeb", help="Company Name"
    )
    check_out_parser = snipeit_subparsers.add_parser(
        "user_del",
        help="Delete new user by providing user First Name and Last Name",
    )
    check_out_parser.add_argument(
        "--first-name", type=str, help="User First Name", required=True
    )
    check_out_parser.add_argument(
        "--last-name", type=str, help="User Last Name", required=True
    )

    check_in_parser = snipeit_subparsers.add_parser(
        "check_in",
        help="Check in an asset by providing the Asset ID or RTE IP",
    )
    check_in_group = check_in_parser.add_mutually_exclusive_group(
        required=True
    )
    check_in_group.add_argument("--asset_id", type=int, help="Asset ID")
    check_in_group.add_argument("--rte_ip", type=str, help="RTE IP address")

    check_in_my_parser = snipeit_subparsers.add_parser(
        "check_in_my", help="Check in all my used assets, except work laptops"
    )
    check_in_my_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skips the confirmation"
    )

    # RTE subcommands
    rte_parser.add_argument(
        "--rte_ip", type=str, help="RTE IP address", required=True
    )
    rte_parser.add_argument(
        "--model",
        type=str,
        help="DUT model. If not given, will attempt to query from Snipe-IT.",
        required=False,
    )
    rte_parser.add_argument(
        "--skip-snipeit",
        action="store_true",
        help=(
            f"Skips Snipe-IT related actions like checkout and check-in. "
            f"Useful for OSFV homelab."
        ),
    )
    rte_subparsers = rte_parser.add_subparsers(
        title="subcommands", dest="rte_cmd", help="RTE subcommands"
    )
    rel_parser = rte_subparsers.add_parser("rel", help="Control RTE relay")
    gpio_parser = rte_subparsers.add_parser("gpio", help="Control RTE GPIO")
    pwr_parser = rte_subparsers.add_parser(
        "pwr", help="Control DUT power via RTE"
    )
    spi_parser = rte_subparsers.add_parser(
        "spi", help="Control SPI lines of RTE"
    )
    serial_parser = rte_subparsers.add_parser(
        "serial", help="Open DUT serial via telnet"
    )
    flash_parser = rte_subparsers.add_parser(
        "flash", help="DUT flash operations"
    )

    # Power subcommands
    pwr_subparsers = pwr_parser.add_subparsers(
        title="subcommands", dest="pwr_cmd"
    )
    power_on_parser = pwr_subparsers.add_parser(
        "on", help="Short power button press, to power on DUT"
    )
    power_on_parser.add_argument(
        "--time",
        type=int,
        default=1,
        help="Power button press time in seconds (default: 1)",
    )
    power_on_ex_parser = pwr_subparsers.add_parser(
        "on_ex", help="Short power button press, to power on DUT"
    )
    power_on_ex_parser.add_argument(
        "--time",
        type=int,
        default=1,
        help="Power button press time in seconds (default: 1) AND verify if power LED did light up",
    )

    power_off_parser = pwr_subparsers.add_parser(
        "off_ex", help="Long power button press, to power off DUT"
    )
    power_off_parser.add_argument(
        "--time",
        type=int,
        default=6,
        help="Power button press time in seconds (default: 6)",
    )
    power_off_ex_parser = pwr_subparsers.add_parser(
        "off",
        help="Long power button press, to power off DUT and verify if power LED did turn off",
    )
    power_off_ex_parser.add_argument(
        "--time",
        type=int,
        default=6,
        help="Power button press time in seconds (default: 6)",
    )

    reset_parser = pwr_subparsers.add_parser(
        "reset", help="Reset button press, to reset DUT"
    )
    reset_parser.add_argument(
        "--time",
        type=int,
        default=1,
        help="Reset button press time in seconds (default: 1)",
    )
    psu_parser = pwr_subparsers.add_parser(
        "psu", help="Generic control interface of the power supply"
    )
    psu_subparsers = psu_parser.add_subparsers(
        title="Power supply commands", dest="psu_cmd"
    )
    psu_subparsers.add_parser("on", help="Turn the power supply on")
    psu_subparsers.add_parser("off", help="Turn the power supply off")
    psu_subparsers.add_parser(
        "get", help="Display information on DUT's power state"
    )
    check_pwr_led_parser = pwr_subparsers.add_parser(
        "pwr_led", help="Check the state of the DUT power LED"
    )

    cmos_reset_subparser = pwr_subparsers.add_parser(
        "reset_cmos", help="Reset the DUT CMOS"
    )

    # GPIO subcommands
    gpio_subparsers = gpio_parser.add_subparsers(
        title="subcommands", dest="gpio_cmd"
    )
    get_gpio_parser = gpio_subparsers.add_parser("get", help="Get GPIO state")
    get_gpio_parser.add_argument("gpio_no", type=int, help="GPIO number")
    set_gpio_parser = gpio_subparsers.add_parser("set", help="Set GPIO state")
    set_gpio_parser.add_argument("gpio_no", type=int, help="GPIO number")
    set_gpio_parser.add_argument(
        "state", choices=["high", "low", "high-z"], help="GPIO state"
    )
    set_gpio_parser = gpio_subparsers.add_parser(
        "list", help="List GPIO states"
    )

    # Relay subcommands
    rel_subparsers = rel_parser.add_subparsers(
        title="subcommands", dest="rel_cmd"
    )
    tgl_rel_parser = rel_subparsers.add_parser(
        "tgl", help="Toggle relay state"
    )
    get_rel_parser = rel_subparsers.add_parser("get", help="Get relay state")
    set_rel_parser = rel_subparsers.add_parser("set", help="Set relay state")
    set_rel_parser.add_argument(
        "state",
        choices=[
            "on",
            "off",
        ],
        help="Relay state",
    )

    # RTE SPI subcommands
    spi_subparsers = spi_parser.add_subparsers(
        title="subcommands", dest="spi_cmd"
    )
    spi_on_parser = spi_subparsers.add_parser("on", help="Enable SPI lines")
    spi_on_parser.add_argument(
        "--voltage",
        type=str,
        default="1.8V",
        help="SPI voltage (default: 1.8V)",
    )
    spi_off_parser = spi_subparsers.add_parser("off", help="Disable SPI lines")

    # RTE flash subcommands
    flash_subparsers = flash_parser.add_subparsers(
        title="subcommands", dest="flash_cmd"
    )
    flash_probe_parser = flash_subparsers.add_parser(
        "probe", help="Flash probe with flashrom"
    )
    flash_read_parser = flash_subparsers.add_parser(
        "read", help="Read from DUT flash with flashrom"
    )
    flash_read_parser.add_argument(
        "--rom",
        type=str,
        default="read.rom",
        help="Path to read firmware file (default: read.rom)",
    )
    flash_write_parser = flash_subparsers.add_parser(
        "write", help="Write to DUT flash with flashrom"
    )
    flash_write_parser.add_argument(
        "--rom",
        type=str,
        default="write.rom",
        help="Path to read firmware file (default: write.rom)",
    )
    flash_write_parser.add_argument(
        "-b",
        "--bios",
        action="store_true",
        help='Adds "-i bios --ifd" to flashrom command',
    )
    flash_write_parser.add_argument(
        "-x",
        "--dry-mecheck",
        help="Failed flash region checks won't forbid flashing",
        action="store_true",
    )
    flash_write_parser.add_argument(
        "-V",
        "--verbosity",
        help="Increase osfv.libs.flash_image verbosity",
        action="store_true",
    )
    flash_erase_parser = flash_subparsers.add_parser(
        "erase", help="Erase DUT flash with flashrom"
    )

    flash_image_check_parser = subparsers.add_parser(
        "flash_image_check",
        help="Check flash image completeness: descriptor & ME region existence",
    )
    flash_image_check_parser.add_argument(
        "--rom",
        type=str,
        required=True,
        help="Path to read firmware file (default: write.rom)",
    )
    flash_image_check_parser.add_argument(
        "-x",
        "--dry-mecheck",
        help="Failed flash region checks won't change exit status",
        action="store_true",
    )
    flash_image_check_parser.add_argument(
        "-V",
        "--verbosity",
        help="Increase osfv.libs.flash_image verbosity",
        action="store_true",
    )
    flash_image_check_parser.add_argument(
        "-l",
        "--list",
        help="list known region names and exit",
        action="store_true",
        dest="list",
    )
    flash_image_check_parser.add_argument(
        "-c",
        "--check",
        help="check named flash region",
        action="append",
        type=str,
        dest="regions_to_check",
    )
    flash_image_check_parser.add_argument(
        "-d",
        "--dump",
        help="dump named flash region",
        action="append",
        type=str,
        dest="regions_to_dump",
    )

    args = parser.parse_args()

    snipeit_api = SnipeIT()

    if args.command == "snipeit":
        if args.snipeit_cmd == "list_used":
            list_used_assets(snipeit_api, args)
        elif args.snipeit_cmd == "list_my":
            list_my_assets(snipeit_api, args)
        elif args.snipeit_cmd == "list_unused":
            list_unused_assets(snipeit_api, args)
        elif args.snipeit_cmd == "list_all":
            list_all_assets(snipeit_api, args)
        elif args.snipeit_cmd == "list_for_zabbix":
            list_for_zabbix(snipeit_api, args)
        elif args.snipeit_cmd == "check_out":
            if args.asset_id:
                check_out_asset(snipeit_api, args.asset_id)
            elif args.rte_ip:
                asset_id = snipeit_api.get_asset_id_by_rte_ip(args.rte_ip)
                if asset_id:
                    check_out_asset(snipeit_api, asset_id)
                else:
                    print(f"No asset found with RTE IP: {args.rte_ip}")
        elif args.snipeit_cmd == "check_in":
            if args.asset_id:
                check_in_asset(snipeit_api, args.asset_id)
            elif args.rte_ip:
                asset_id = snipeit_api.get_asset_id_by_rte_ip(args.rte_ip)
                if asset_id:
                    check_in_asset(snipeit_api, asset_id)
                else:
                    print(f"No asset found with RTE IP: {args.rte_ip}")
        elif args.snipeit_cmd == "check_in_my":
            check_in_my(snipeit_api, args)
        elif args.snipeit_cmd == "user_add":
            snipeit_api.user_add(
                args.first_name, args.last_name, args.company_name
            )
        elif args.snipeit_cmd == "user_del":
            snipeit_api.user_del(args.first_name, args.last_name)
        elif args.snipeit_cmd == "update_zabbix":
            update_zabbix_assets(snipeit_api)

    elif args.command == "rte":
        if not args.skip_snipeit:
            asset_id = snipeit_api.get_asset_id_by_rte_ip(args.rte_ip)
            if not asset_id:
                print(f"No asset found with RTE IP: {args.rte_ip}")

        if args.model:
            print(f"DUT model retrieved from cmdline, skipping Snipe-IT query")
            dut_model_name = args.model
        else:
            if not args.skip_snipeit:
                status, dut_model_name = snipeit_api.get_asset_model_name(
                    asset_id
                )
                if status:
                    print(
                        f"DUT model retrieved from snipeit: {dut_model_name}"
                    )
                else:
                    exit(
                        f"failed to retrieve model name from snipe-it. check "
                        f"again arguments, or try providing model manually."
                    )
            else:
                exit(f"model name not present. check again arguments.")
        sonoff, sonoff_ip = utils.init_sonoff(None, args.rte_ip, snipeit_api)
        rte = RTE(args.rte_ip, dut_model_name, sonoff)

        if not args.skip_snipeit:
            print(
                f"Using rte command is invasive action, checking first if the "
                f"device is not used..."
            )
            already_checked_out = check_out_asset(snipeit_api, asset_id)

        if args.rte_cmd == "rel":
            # Handle RTE relay related commands
            if args.rel_cmd == "tgl":
                relay_toggle(rte, args)
            elif args.rel_cmd == "get":
                relay_get(rte, args)
            elif args.rel_cmd == "set":
                relay_set(rte, args)
        elif args.rte_cmd == "gpio":
            # Handle RTE GPIO related commands
            if args.gpio_cmd == "get":
                gpio_get(rte, args)
            elif args.gpio_cmd == "set":
                gpio_set(rte, args)
            elif args.gpio_cmd == "list":
                gpio_list(rte, args)
        elif args.rte_cmd == "pwr":
            # Handle RTE power related commands
            if args.pwr_cmd == "on":
                power_on(rte, args)
            elif args.pwr_cmd == "off":
                power_off(rte, args)
            if args.pwr_cmd == "on_ex":
                power_on_ex(rte, args)
            elif args.pwr_cmd == "off_ex":
                power_off_ex(rte, args)
            elif args.pwr_cmd == "reset":
                reset(rte, args)
            elif args.pwr_cmd == "pwr_led":
                check_pwr_led(rte, args)
            elif args.pwr_cmd == "psu":
                if args.psu_cmd == "on":
                    psu_on(rte, args)
                elif args.psu_cmd == "off":
                    psu_off(rte, args)
                elif args.psu_cmd == "get":
                    psu_get(rte, args)
            elif args.pwr_cmd == "reset_cmos":
                reset_cmos(rte, args)
        elif args.rte_cmd == "serial":
            open_dut_serial(rte, args)
        elif args.rte_cmd == "spi":
            if args.spi_cmd == "on":
                spi_on(rte, args)
            elif args.spi_cmd == "off":
                spi_off(rte, args)
        elif args.rte_cmd == "flash":
            if args.flash_cmd == "probe":
                flash_probe(rte, args)
            elif args.flash_cmd == "read":
                flash_read(rte, args)
            elif args.flash_cmd == "write":
                flash_write(rte, args)
            elif args.flash_cmd == "erase":
                flash_erase(rte, args)

        if not args.skip_snipeit:
            if already_checked_out:
                print(
                    f"Since the asset {asset_id} has been checkout manually "
                    f"by you prior running this script, it will NOT be checked "
                    f"in automatically. Please return the device when work is "
                    f"finished."
                )
            else:
                print(
                    f"Since the asset {asset_id} has been checkout "
                    f"automatically by this script, it is automatically "
                    f"checked in as well."
                )
                check_in_asset(snipeit_api, asset_id)
    elif args.command == "sonoff":
        sonoff_ip = ""

        if args.sonoff_ip:
            sonoff_ip = args.sonoff_ip
        elif args.rte_ip:
            sonoff_ip = snipeit_api.get_sonoff_ip_by_rte_ip(args.rte_ip)
            if not sonoff_ip:
                print(f"No Sonoff Device found with RTE IP: {args.rte_ip}")

        asset_id = snipeit_api.get_asset_id_by_sonoff_ip(sonoff_ip)
        if not asset_id:
            print(f"No asset found with RTE IP: {args.rte_ip}")

        print(
            f"Using rte command is invasive action, checking first if the "
            f"device is not used..."
        )
        already_checked_out = check_out_asset(snipeit_api, asset_id)

        sonoff = SonoffDevice(sonoff_ip)

        if args.sonoff_cmd == "on":
            sonoff_on(sonoff, args)
        if args.sonoff_cmd == "off":
            sonoff_off(sonoff, args)
        if args.sonoff_cmd == "get":
            sonoff_get(sonoff, args)
        if args.sonoff_cmd == "tgl":
            sonoff_tgl(sonoff, args)

        if already_checked_out:
            print(
                f"Since the asset {asset_id} has been checkout manually by "
                f"you prior running this script, it will NOT be checked in "
                f"automatically. Please return the device when work is "
                f"finished."
            )
        else:
            print(
                f"Since the asset {asset_id} has been checkout automatically "
                f"by this script, it is automatically checked in as well."
            )
            check_in_asset(snipeit_api, asset_id)
    elif args.command == "flash_image_check":
        flash_image_check(args)
    elif args.command == "list_models":
        list_models(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

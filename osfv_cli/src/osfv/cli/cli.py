#!/usr/bin/env python3

import json
from collections.abc import Callable
from copy import copy
from dataclasses import dataclass, field
from functools import partial, wraps
from importlib import metadata
from pathlib import Path
from time import sleep
from typing import Annotated, Literal, cast

import pexpect
import requests
import typer
from typer import Argument, Context, Option

from osfv.libs import utils
from osfv.libs.models import Models
from osfv.libs.rte import RTE
from osfv.libs.snipeit_api import SnipeIT
from osfv.libs.sonoff_api import SonoffDevice
from osfv.libs.zabbix import Zabbix


class API:
    """store API instances created e.g. in callbacks"""

    def __init__(self) -> None:
        self._sonoff_api: SonoffDevice | None = None
        self._snipeit_api: SnipeIT | None = None
        self._rte_api: RTE | None = None

    @property
    def sonoff_api(self) -> SonoffDevice:
        """Return SonoffDevice instance or raise error if None is set.

        Returns:
            SonoffDevice: SonoffDevice instance
        """
        assert self._sonoff_api is not None
        return self._sonoff_api

    @property
    def snipeit_api(self) -> SnipeIT:
        """Return SnipeIT instance or raise error if None is set.

        Returns:
            SnipeIT: SnipeIT instance
        """
        assert self._snipeit_api is not None
        return self._snipeit_api

    @property
    def rte_api(self) -> RTE:
        """Return RTE instance or raise error if None is set.

        Returns:
            RTE: RTE instance
        """
        assert self._rte_api is not None
        return self._rte_api

    def get_or_create_snipeit(self) -> SnipeIT:
        """returns snipeit_api instance, creates it if necessary

        Returns:
            SnipeIT: SnipeIT API instance
        """
        if self._snipeit_api is None:
            self._snipeit_api = SnipeIT()
        return self._snipeit_api


@dataclass
class Hooks:
    setup: Callable[[], tuple[bool, int | None]]
    cleanup: Callable[[bool, int | None], None]
    _already_ran: bool = field(default=False, init=False)


def with_setup(func):
    """Use this decorator to call setup and cleanup check_out/check_in function

    Requires the first argument of the decorated function to be of typer.Context
    type.

    Calls setup if ctx.obj is instance of Hooks, and setups cleanup to be called
    during context tear down. Makes sure to only do it once even if mutliple
    decorated functions are called.

    Use this decorator so you don't have to setup/cleanup stuff manually in
    each command or run heavy setup function before all arguments are validated.

    ctx.obj can be set in callback subcommand (check rte_options function for
    examples)
    """

    @wraps(func)
    def wrapper(ctx: Context, *args, **kwargs):
        if isinstance(ctx.obj, Hooks) and not ctx.obj._already_ran:
            ctx.obj._already_ran = True
            checked_out, asset_id = ctx.obj.setup()
            ctx.call_on_close(partial(ctx.obj.cleanup, checked_out, asset_id))
        return func(ctx, *args, **kwargs)

    return wrapper


def check_in_cleanup(checked_out: bool, asset_id: int | None):
    if checked_out and asset_id is not None:
        _check_in_asset(apis.get_or_create_snipeit(), asset_id)


apis = API()

## Intermediate subcommands


def add_typer(help: str, name: str, target_typer: typer.Typer):
    new_typer = typer.Typer(help=help)
    target_typer.add_typer(new_typer, name=name)
    return new_typer


app = typer.Typer(
    no_args_is_help=True,
    help="Open Source Firmware Validation CLI",
    context_settings={"help_option_names": ["-h", "--help"]},
)

## root subcommands
snipeit_t = add_typer("Snipe-IT commands", "snipeit", app)
rte_t = add_typer("RTE commands", "rte", app)
sonoff_t = add_typer("Sonoff commands", "sonoff", app)
# list_models and flash_image_check are final subcommands
## rte subcommands
rte_rel = add_typer("Control RTE relay", "rel", rte_t)
rte_gpio = add_typer("Control RTE GPIO", "gpio", rte_t)
rte_pwr = add_typer("Control DUT power via RTE", "pwr", rte_t)
rte_spi = add_typer("Control SPI lines of RTE", "spi", rte_t)
rte_flash = add_typer("DUT flash operations", "flash", rte_t)
# rte serial is final subcommand so it is defined with other commands
## rte pwr subcommands
rte_pwr_psu = add_typer("Generic control interface of the power supply", "psu", rte_pwr)


def main():
    app()


def print_version(version: bool):
    """Print version and exit"""
    if version:
        print(metadata.version("osfv"))
        raise typer.Exit()


## root commands
@app.callback()
def root_options(
    _: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="show program's version number and exit",
            is_eager=True,
            callback=print_version,
        ),
    ] = False,
):
    pass


@app.command("list_models")
def list_models():
    """List of supported models"""
    models = Models()
    models.list_models()


def list_known_regions(list_regions: bool):
    """List known region names and exit

    Args:
        list_regions (bool): Whether to list regions
    """
    if list_regions:
        print("Known flash regions:")
        for reg_name in utils.get_list_of_known_image_regions():
            print(reg_name)
        raise typer.Exit()


@app.command("flash_image_check")
def flash_image_check(
    rom: Annotated[
        Path,
        Option(
            "--rom",
            help="Path to read firmware file",
            metavar="ROM",
            exists=True,
            dir_okay=False,
        ),
    ] = Path("write.rom"),
    dry_mecheck: Annotated[
        bool,
        Option(
            "--dry-mecheck",
            "-x",
            help="Failed flash region checks won't change exit status",
        ),
    ] = False,
    verbosity: Annotated[
        bool,
        Option("--verbosity", "-V", help="Increase osfv.libs.flash_image verbosity"),
    ] = False,
    _: Annotated[
        bool,
        Option(
            "--list",
            "-l",
            help="list known region names and exit",
            is_eager=True,
            callback=list_known_regions,
        ),
    ] = False,
    regions_to_check: Annotated[
        list[str] | None,
        Option(
            "--check",
            "-c",
            help="check named flash region",
            metavar="REGIONS_TO_CHECK",
            show_default="me",
        ),
    ] = None,
    regions_to_dump: Annotated[
        list[str] | None,
        Option(
            "--dump", "-d", help="dump named flash region", metavar="REGIONS_TO_DUMP"
        ),
    ] = None,
):
    """Checks for existence & sane content of ME region in flash image"""
    if regions_to_dump:
        utils.dump_flash_image_regions(rom, verbosity, regions_to_dump)
    if regions_to_check is None:
        regions_to_check = ["me"]
    if (
        utils.check_flash_image_regions(rom, dry_mecheck, verbosity, regions_to_check)
        == False
    ):
        print(
            "Do not flash full image, unless you are skipping empty regions, and know what you are doing!"
        )
        raise typer.Exit(1)


## snipeit commands
@snipeit_t.command("list_used")
def list_used_assets(
    dump_json: Annotated[bool, Option("--json", help="Dump assets as JSON")] = False,
):
    """List all already used assets"""
    all_assets = apis.get_or_create_snipeit().get_all_assets()
    used_assets = [asset for asset in all_assets if asset["assigned_to"] is not None]

    if not used_assets:
        print("No used assets found.")
        return

    if dump_json:
        print(json.dumps(used_assets))
    else:
        for asset in used_assets:
            print_asset_details(asset)


@snipeit_t.command("list_my", help="List all my used assets")
def list_my_assets(
    dump_json: Annotated[bool, Option("--json", help="Dump assets as JSON")] = False,
) -> bool:
    """
    List all my used assets

    Returns:
        Boolean: False if no assets were assigned to the user, True otherwise
    """
    my_assets = get_my_assets(apis.get_or_create_snipeit())

    if not my_assets:
        print("No used assets found.")
        return False

    if dump_json:
        print(json.dumps(my_assets))
    else:
        for asset in my_assets:
            print_asset_details(asset)
    return True


@snipeit_t.command("list_unused")
def list_unused_assets(
    dump_json: Annotated[bool, Option("--json", help="Dump assets as JSON")] = False,
):
    """List all unused assets"""
    all_assets = apis.get_or_create_snipeit().get_all_assets()
    unused_assets = [asset for asset in all_assets if asset["assigned_to"] is None]

    if not unused_assets:
        print("No unused assets found.")
        return

    if dump_json:
        print(json.dumps(unused_assets))
    else:
        for asset in unused_assets:
            print_asset_details(asset)


@snipeit_t.command("list_all")
def list_all_assets(
    dump_json: Annotated[bool, Option("--json", help="Dump assets as JSON")] = False,
):
    """List all assets"""
    all_assets = apis.get_or_create_snipeit().get_all_assets()

    if not all_assets:
        print("No assets found.")
        return

    if dump_json:
        print(json.dumps(all_assets))
    else:
        for asset in all_assets:
            print_asset_details(asset)


@snipeit_t.command("list_for_zabbix")
def list_for_zabbix():
    """List assets in a format suitable for Zabbix integration"""
    all_assets = apis.get_or_create_snipeit().get_all_assets()

    if all_assets:
        for asset in all_assets:
            print_asset_details_for_zabbix(asset)
    else:
        print("No assets found.")


@snipeit_t.command("update_zabbix", help="Syncs Zabbix assets with SnipeIT ones")
def update_zabbix_assets():
    """
    Updates Zabbix with the latest asset data from Snipe-IT, ensuring the IP addresses
    are synchronized between Snipe-IT and Zabbix.
    """
    zabbix = Zabbix()
    all_assets = apis.get_or_create_snipeit().get_all_assets()

    current_zabbix_assets = zabbix.get_all_hosts()
    # snipeit assets but converted to zabbix-form assets
    snipeit_assets = {}

    update_available = False

    if all_assets:
        for asset in all_assets:
            snipeit_assets.update(get_zabbix_compatible_assets_from_asset(asset))

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
        if any(symbol in snipeit_assets_keys[i] for symbol in forbidden_symbols):
            print(
                f"{snipeit_assets_keys[i]} contains forbidden symbols! They "
                f"are going to be changed to '_'."
            )
            new_key = copy(snipeit_assets_keys[i])
            for s in forbidden_symbols:
                new_key = new_key.replace(s, "_")

            snipeit_assets[new_key] = snipeit_assets.pop(snipeit_assets_keys[i])

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

    common_keys = set(snipeit_assets.keys()) & set(current_zabbix_assets.keys())

    if keys_not_present_in_zabbix.__len__() > 0:
        print("Assets not present in Zabbix (these will be added):")
        print("\n".join(keys_not_present_in_zabbix))

    if keys_not_present_in_snipeit.__len__() > 0:
        print("\nAssets present in Zabbix but not in SnipeIT (these will be removed):")
        print("\n".join(keys_not_present_in_snipeit))

    print()
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


@snipeit_t.command("check_out")
def check_out_asset(
    asset_id: Annotated[
        int | None, Option("--asset_id", help="Asset ID", metavar="ASSET_ID")
    ] = None,
    rte_ip: Annotated[
        str | None, Option("--rte_ip", help="RTE IP address", metavar="RTE_IP")
    ] = None,
):
    """Check out an asset by providing the Asset ID or RTE IP

    It checks if the asset is already checked out by the user.
    """
    snipeit_api = apis.get_or_create_snipeit()
    asset_id = validate_and_return_asset_id(snipeit_api, asset_id, rte_ip)
    _check_out_asset(snipeit_api, asset_id)


@snipeit_t.command("check_in")
def check_in_asset(
    asset_id: Annotated[
        int | None, Option("--asset_id", help="Asset ID", metavar="ASSET_ID")
    ] = None,
    rte_ip: Annotated[
        str | None, Option("--rte_ip", help="RTE IP address", metavar="RTE_IP")
    ] = None,
):
    """Check in an asset by providing the Asset ID or RTE IP"""
    snipeit_api = apis.get_or_create_snipeit()
    asset_id = validate_and_return_asset_id(snipeit_api, asset_id, rte_ip)
    if not _check_in_asset(snipeit_api, asset_id):
        raise typer.Exit(1)


@snipeit_t.command("check_in_my")
def check_in_my(
    dump_json: Annotated[bool, Option("--json", help="Dump assets as JSON")] = False,
    yes: Annotated[bool, Option("--yes", "-y", help="Skips the confirmation")] = False,
):
    """
    Lists all assets assigned to the current user, checks in all of them
    except those which are in a category listed in `categories_to_ignore`.
    """
    categories_to_ignore = ["Employee Laptop"]
    snipeit_api = apis.get_or_create_snipeit()
    my_assets = get_my_assets(snipeit_api)

    my_assets = [
        asset
        for asset in my_assets
        if not set(asset["category"].values()) & set(categories_to_ignore)
    ]
    if not list_my_assets(dump_json):
        raise typer.Exit()

    if not yes:
        choice = typer.confirm(
            f"Are you sure you want to check in {len(my_assets)} assets? [y/N]"
        )

        if not choice:
            print(f"Checking in {len(my_assets)} assets aborted.")
            raise typer.Exit()

    failed = []
    for asset in my_assets:
        if not _check_in_asset(snipeit_api, asset["id"]):
            failed = failed.append(asset)

    if failed:
        print(f"Failed to check-in {len(failed)} assets:")
    else:
        print(f"{len(my_assets)} assets checked in successfully.")


@snipeit_t.command("user_add")
def user_add(
    first_name: Annotated[
        str, Option("--first-name", help="User First Name", metavar="FIRST_NAME")
    ],
    last_name: Annotated[
        str, Option("--last-name", help="User Last Name", metavar="LAST_NAME")
    ],
    company_name: Annotated[
        str, Option("--company-name", help="Company Name", metavar="COMPANY_NAME")
    ],
):
    """Add a new user by providing user First Name, Last Name and Company Name"""
    apis.get_or_create_snipeit().user_add(first_name, last_name, company_name)


@snipeit_t.command("user_del")
def user_del(
    first_name: Annotated[
        str, Option("--first-name", help="User First Name", metavar="FIRST_NAME")
    ],
    last_name: Annotated[
        str, Option("--last-name", help="User Last Name", metavar="LAST_NAME")
    ],
):
    """Delete new user by providing user First Name and Last Name"""
    apis.get_or_create_snipeit().user_del(first_name, last_name)


## rte commands
def setup_rte_subcommand(
    rte_ip: str, model: str | None, skip_snipeit: bool
) -> tuple[bool, int | None]:
    """Validate arguments, setup needed resources

    Sets up snipeit, sonoff, and rte in `apis`, checkes out asset if required

    Args:
        rte_ip (str): RTE IP Address
        model (str | None): Model name, used if skipping snipeit
        skip_snipeit (bool): Whether to skip snipeit requests

    Raises:
        typer.Exit: When setup/checkout fails

    Returns:
        tuple[bool, str]: (asset was checked_out?, asset_id)
    """
    snipeit_api: SnipeIT | None = None
    asset_id: int | None = None
    dut_model_name: str | None = None
    if not skip_snipeit:
        snipeit_api = apis.get_or_create_snipeit()
        asset_id = snipeit_api.get_asset_id_by_rte_ip(rte_ip)
        if asset_id is None:
            print(f"No asset found with RTE IP: {rte_ip}")
            raise typer.Exit(1)
    if model:
        print("DUT model retrieved from cmdline, skipping Snipe-IT query")
        dut_model_name = model
    else:
        if not skip_snipeit:
            status, dut_model_name = apis.snipeit_api.get_asset_model_name(asset_id)
            if status:
                print(f"DUT model retrieved from snipeit: {dut_model_name}")
            else:
                print(
                    "failed to retrieve model name from snipe-it. check "
                    "again arguments, or try providing model manually."
                )
                raise typer.Exit(1)
        else:
            print("`--model MODEL` is required when skipping snipeit.")
            raise typer.Exit(1)
    # TODO: Add sonoff ip argument
    apis._sonoff_api, _ = utils.init_sonoff(None, rte_ip, snipeit_api)
    apis._rte_api = RTE(rte_ip, dut_model_name, apis._sonoff_api)

    if not skip_snipeit:
        assert isinstance(asset_id, int)
        print(
            "Using rte command is invasive action, checking first if the "
            "device is not used..."
        )
        already_checked_out = _check_out_asset(apis.snipeit_api, cast(int, asset_id))
        return not already_checked_out, asset_id
    return False, None


@rte_t.callback()
def rte_options(
    ctx: Context,
    rte_ip: Annotated[str, Option("--rte_ip", help="RTE IP address", metavar="RTE_IP")],
    model: Annotated[
        str | None,
        Option(
            "--model",
            help="DUT model. If not given, will attempt to query from Snipe-IT.",
            metavar="MODEL",
        ),
    ] = None,
    skip_snipeit: Annotated[
        bool,
        Option(
            "--skip-snipeit",
            help="Skips Snipe-IT related actions like checkout and check-in. Useful for OSFV homelab.",
        ),
    ] = False,
):
    ctx.obj = Hooks(
        setup=partial(setup_rte_subcommand, rte_ip, model, skip_snipeit),
        cleanup=check_in_cleanup,
    )


@rte_t.command("serial")
@with_setup
def open_dut_serial(ctx: Context):
    """Open DUT serial via telnet

    Open a Telnet session to interact with the DUT serial interface.
    """
    host = apis.rte_api.rte_ip
    port = 13541

    print(f"Opening telnet session with: {host}:{port}")
    print("Press Ctrl+] to exit")
    # Connect to the Telnet server
    tn = pexpect.spawn(f"telnet {host} {port}")

    # Enter the interactive shell
    tn.interact()


## rte rel commands
@rte_rel.command("tgl")
@with_setup
def relay_toggle(ctx: Context):
    """Toggle relay state"""
    rte = apis.rte_api
    state_str = rte.relay_get()
    if state_str == RTE.PSU_STATE_OFF:
        new_state_str = RTE.PSU_STATE_ON
    else:
        new_state_str = RTE.PSU_STATE_OFF
    rte.relay_set(new_state_str)
    state = rte.relay_get()
    print(f"Relay state toggled. New state: {state}")


@rte_rel.command("get")
@with_setup
def relay_get(ctx: Context):
    """Get relay state"""
    state = apis.rte_api.relay_get()
    print(f"Relay state: {state}")


@rte_rel.command("set")
@with_setup
def relay_set(
    ctx: Context, state: Annotated[Literal["on", "off"], Argument(help="Relay state")]
):
    """Set relay state"""
    rte = apis.rte_api
    rte.relay_set(state)
    current_state = rte.relay_get()
    print(f"Relay state set to {current_state}")


## rte gpio commands
@rte_gpio.command("get")
@with_setup
def gpio_get(ctx: Context, gpio_no: Annotated[int, Argument(help="GPIO number")]):
    """Get GPIO state"""
    state = apis.rte_api.gpio_get(gpio_no)
    print(f"GPIO {gpio_no} state: {state}")


@rte_gpio.command("set")
@with_setup
def gpio_set(
    ctx: Context,
    gpio_no: Annotated[int, Argument(help="GPIO number")],
    state: Annotated[Literal["high", "low", "high-z"], Argument(help="GPIO state")],
):
    """Set GPIO state"""
    rte = apis.rte_api
    rte.gpio_set(gpio_no, state)
    state = rte.gpio_get(gpio_no)
    print(f"GPIO {gpio_no} state set to {state}")


@rte_gpio.command("list")
@with_setup
def gpio_list(ctx: Context):
    """List GPIO states"""
    response = json.dumps(apis.rte_api.gpio_list(), indent=4)
    print("GPIO list")
    print(response)


## rte pwr commands
@rte_pwr.command("on")
@with_setup
def power_on(
    ctx: Context,
    time: Annotated[
        int,
        Option(
            "--time", help="Power button press time in seconds", metavar="TIME", min=1
        ),
    ] = 1,
):
    """Short power button press, to power on DUT"""
    rte = apis.rte_api
    state = rte.psu_get()
    if state != rte.PSU_STATE_ON:
        print(f"Power supply state: {state} !")
        print(
            "If you wanted to power on the DUT, you need to enable power suppl"
            'y first ("pwr psu on"), pushing the power button is not enough!'
        )
    print("Powering on...")
    rte.power_on(time)


@rte_pwr.command("on_ex")
@with_setup
def power_on_ex(
    ctx: Context,
    time: Annotated[
        int,
        Option(
            "--time", help="Power button press time in seconds", metavar="TIME", min=1
        ),
    ] = 1,
):
    """Short power button press, to power on DUT, and verify if power LED did turn off"""
    power_on(ctx, time)
    for _ in range(20):
        if check_pwr_led(ctx) == "high":
            print("Power on successful.")
            return True
        sleep(0.25)
    print("Power on failed.")
    return False


@rte_pwr.command("off")
@with_setup
def power_off(
    ctx: Context,
    time: Annotated[
        int,
        Option(
            "--time", help="Power button press time in seconds", metavar="TIME", min=1
        ),
    ] = 1,
):
    """Long power button press, to power off DUT"""
    print("Powering off...")
    apis.rte_api.power_off(time)


@rte_pwr.command("off_ex")
@with_setup
def power_off_ex(
    ctx: Context,
    time: Annotated[
        int,
        Option(
            "--time", help="Power button press time in seconds", metavar="TIME", min=1
        ),
    ] = 1,
):
    """Long power button press, to power off DUT, and verify if power LED did turn off"""
    power_off(ctx, time)
    for _ in range(20):
        if check_pwr_led(ctx) == "low":
            print("Power off successful.")
            raise typer.Exit()
        sleep(0.25)
    print("Power off failed.")
    raise typer.Exit(1)


@rte_pwr.command()
@with_setup
def reset(
    ctx: Context,
    time: Annotated[
        int,
        Option(
            "--time", help="Power button press time in seconds", metavar="TIME", min=1
        ),
    ] = 1,
):
    """Reset button press, to reset DUT"""
    print("Pressing reset button...")
    apis.rte_api.reset(time)


@rte_pwr.command("pwr_led")
@with_setup
def check_pwr_led(ctx: Context):
    """Check the state of the DUT power LED"""
    rte = apis.rte_api
    state = rte.gpio_get(RTE.GPIO_PWR_LED)
    polarity = rte.dut_data.get("pwr_led", {}).get("polarity")
    if polarity and polarity == "active low":
        if state == "high":
            state = "low"
        else:
            state = "high"

    print(f"Power LED state: {'ON' if state == 'high' else 'OFF'}")
    return state


@rte_pwr.command()
@with_setup
def reset_cmos(ctx: Context):
    """Reset the DUT CMOS"""
    print("Clearing CMOS...")
    apis.rte_api.reset_cmos()


## rte pwr psu commands
@rte_pwr_psu.command("on")
@with_setup
def psu_on(ctx: Context):
    """Turn the power supply on"""
    print("Enabling power supply...")
    apis.rte_api.psu_on()


@rte_pwr_psu.command("off")
@with_setup
def psu_off(ctx: Context):
    """Turn the power supply off"""
    print("Disabling power supply...")
    apis.rte_api.psu_off()


@rte_pwr_psu.command("get")
@with_setup
def psu_get(ctx: Context):
    """Display information on DUT's power state"""
    state = apis.rte_api.psu_get()
    print(f"Power supply state: {state}")


## rte spi commands
@with_setup
@rte_spi.command("on")
def spi_on(ctx: Context):
    """Enable SPI lines"""
    print("Enabling SPI...")
    apis.rte_api.spi_enable()


@rte_spi.command("off")
@with_setup
def spi_off(ctx: Context):
    """Disable SPI lines"""
    print("Disabling SPI...")
    apis.rte_api.spi_disable()


## rte flash commands
@rte_flash.command("probe")
@with_setup
def flash_probe(ctx: Context):
    """Flash probe with flashrom"""
    print("Probing flash...")
    apis.rte_api.flash_probe()


@rte_flash.command("read")
@with_setup
def flash_read(
    ctx: Context,
    rom: Annotated[
        Path,
        Option(
            "--rom",
            help="Path to read firmware file",
            metavar="ROM",
            dir_okay=False,
            writable=True,
        ),
    ] = Path("read.rom"),
):
    """Read from DUT flash with flashrom"""
    print("Reading from flash...")
    apis.rte_api.flash_read(rom)
    print(f"Read flash content saved to {rom}")


@rte_flash.command("write")
@with_setup
def flash_write(
    ctx: Context,
    rom: Annotated[
        Path,
        Option(
            "--rom", help="Path to read firmware file", metavar="ROM", dir_okay=False
        ),
    ] = Path("write.rom"),
    bios: Annotated[
        bool,
        Option(
            "--bios",
            "-b",
            help='Adds "-i bios --ifd" to flashrom command',
            dir_okay=False,
        ),
    ] = False,
    dry_mecheck: Annotated[
        bool,
        Option(
            "--dry-mecheck",
            "-x",
            help="Failed flash region checks won't change exit status",
        ),
    ] = False,
    verbosity: Annotated[
        bool,
        Option("--verbosity", "-V", help="Increase osfv.libs.flash_image verbosity"),
    ] = False,
):
    """Write to DUT flash with flashrom"""
    if utils.check_flash_image_regions(rom, dry_mecheck, verbosity) == False:
        print(
            "FATAL: Image could not be loaded, or some image's regions are empty, despite being defined in the flash descriptor. "
            "Flashing full image in this form on Intel platform will result in a bricked platform. "
            "If you wish to continue anyway (e.g. when using AMD platform), pass the -x option to skip the check. "
            "When using Intel platform, you probably also want to pass the -b option to flash BIOS region only, "
            "leaving other regions in platform's flash (such as ME) intact."
        )
        raise typer.Exit(1)
    print(f"Writing {rom} to flash...")
    rc = apis.rte_api.flash_write(rom, bios)
    if rc == 0:
        print("Flash written successfully")
    else:
        print(f"Flash write failed with code {rc}")


@rte_flash.command("erase")
@with_setup
def flash_erase(ctx):
    """Erase DUT flash with flashrom"""
    print("Erasing DUT flash...")
    apis.rte_api.flash_erase()
    print("Flash erased")


## sonoff commands


def sonoff_setup(sonoff_ip: str | None, rte_ip: str | None) -> tuple[bool, int]:
    if not sonoff_ip:
        if not rte_ip:
            print("Either sonoff_ip or rte_ip is required")
            raise typer.Exit(1)
        sonoff_ip = apis.get_or_create_snipeit().get_sonoff_ip_by_rte_ip(rte_ip)
        if not sonoff_ip:
            print(f"No Sonoff Device found with RTE IP: {rte_ip}")
            raise typer.Exit(1)

    asset_id = apis.get_or_create_snipeit().get_asset_id_by_sonoff_ip(sonoff_ip)
    if asset_id is None:
        print(f"No asset found with Sonoff IP: {sonoff_ip}")
        raise typer.Exit(1)

    print(
        "Using rte command is invasive action, checking first if the "
        "device is not used..."
    )
    already_checked_out = _check_out_asset(apis.snipeit_api, asset_id)
    apis._sonoff_api = SonoffDevice(sonoff_ip)
    return not already_checked_out, asset_id


@sonoff_t.callback()
def sonoff_options(
    ctx: Context,
    sonoff_ip: Annotated[
        str | None, Option("--rte_ip", help="Sonoff IP address", metavar="SONOFF_IP")
    ] = None,
    rte_ip: Annotated[
        str | None, Option("--rte_ip", help="RTE IP address", metavar="RTE_IP")
    ] = None,
):
    ctx.obj = Hooks(
        setup=partial(sonoff_setup, sonoff_ip, rte_ip), cleanup=check_in_cleanup
    )


@sonoff_t.command("on")
@with_setup
def sonoff_on(ctx: Context):
    """Turn Sonoff ON"""
    print("Turning on Sonoff power switch...")
    try:
        response = apis.sonoff_api.turn_on()
        print(response)
    except requests.exceptions.RequestException as e:
        print(f"Failed to turn on Sonoff power switch. Error: {e}")


@sonoff_t.command("off")
@with_setup
def sonoff_off(ctx: Context):
    """Turn Sonoff OFF"""
    print("Turning off Sonoff power switch...")
    try:
        response = apis.sonoff_api.turn_off()
        print(response)
    except requests.exceptions.RequestException as e:
        print(f"Failed to turn off Sonoff power switch. Error: {e}")


@sonoff_t.command("tgl")
@with_setup
def sonoff_tgl(ctx: Context):
    """Toggle Sonoff state"""
    print("Toggling Sonoff power switch state...")
    try:
        sonoff_api = apis.sonoff_api
        current_state = sonoff_api.get_state()

        if current_state == "ON":
            _response = sonoff_api.turn_off()
            print("Sonoff power switch state toggled off.")
        elif current_state == "OFF":
            _response = sonoff_api.turn_on()
            print("Sonoff power switch state toggled on.")
        else:
            print(f"Unexpected Sonoff power switch state: {current_state}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to toggle Sonoff power switch state. Error: {e}")


@sonoff_t.command("get")
@with_setup
def sonoff_get(ctx: Context):
    """Get Sonoff state"""
    print("Getting Sonoff power switch state...")
    try:
        state = apis.sonoff_api.get_state()
        print(f"Sonoff power switch state: {state}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to get Sonoff power switch state. Error: {e}")


def validate_and_return_asset_id(
    snipeit_api: SnipeIT, asset_id: int | None, rte_ip: str | None
) -> int:
    """Check which argument is set and return asset_id based on it

    If both arguments are the same (None or str) then raise typer.Exit, else
    return asset_id or try to turn rte_ip to assed_id and return it.
    Raise typer.Exit if cannot turn rte_ip to asset_id.

    Args:
        snipeit_api (SnipeIT): SnipeIT instance
        asset_id (str | None): Asset ID
        rte_id (str | None): RTE IP address

    Returns:
        str: Found asset_id or None
    """
    if isinstance(asset_id, int) and isinstance(rte_ip, str):
        print("Only asset_id or rte_ip is allowed, not both")
        raise typer.Exit(1)
    if asset_id is None and rte_ip is None:
        print("Either asset_id or rte_ip is required")
        raise typer.Exit(1)

    if rte_ip is not None:
        asset_id = snipeit_api.get_asset_id_by_rte_ip(rte_ip)
        if asset_id is None:
            print(f"No asset found with RTE IP: {rte_ip}")
            raise typer.Exit(1)
    assert asset_id is not None
    return asset_id


def _check_out_asset(snipeit_api: SnipeIT, asset_id: int) -> bool:
    """Check out an asset by providing the Asset ID

    It checks if the asset is already checked out by the user.

    Args:
        snipeit_api (SnipeIT): SnipeIT instance
        asset_id (str): Asset ID to check-out

    Raises:
        typer.Exit: If check-out failed

    Returns:
        bool: True if asset was already checked-out
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
        print(
            "Exiting to avoid conflict. Check who is working on this device"
            " and contact them first."
        )
        raise typer.Exit(1)

    return already_checked_out


def _check_in_asset(snipeit_api: SnipeIT, asset_id: int) -> bool:
    """Check in an asset by providing the Asset ID

    This method attempts to check in the specified asset identified by `asset_id` by making an HTTP POST request.
    If the check-in is successful, it returns True.
    If the check-in fails, it returns False and prints the error message from the API.
    Args:
        snipeit_api (SnipeIT): SnipeIT instance
        asset_id (str): Asset ID to check-in

    Returns:
        bool: Whether check-in succeeded
    """
    success, data = snipeit_api.check_in_asset(asset_id)

    if success:
        print(f"Asset {asset_id} successfully checked in.")
        return True
    else:
        print(f"Error checking in asset {asset_id}")
        print(f"Response data: {data}")
        return False


def get_my_assets(snipeit_api: SnipeIT):
    """
    Gets a list of assets assigned to the current user

    Args:
        snipeit_api: The API client used to interact with the Snipe-IT API.

    Returns:
        List of assets assigned to the current user
    """
    all_assets = snipeit_api.get_all_assets()
    used_assets = [asset for asset in all_assets if asset["assigned_to"] is not None]
    return [
        asset
        for asset in used_assets
        if asset["assigned_to"]["id"] is snipeit_api.cfg_user_id
    ]


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
        f"Asset Tag: {asset['asset_tag']}, Asset ID: {asset['id']},"
        f"Name: {asset['name']}, Serial: {asset['serial']}"
    )

    if asset["assigned_to"]:
        print(f"Assigned to: {asset['assigned_to']['name']}")

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
                    key = f"{asset['asset_tag']}_{field_name}".replace(" ", "_")
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
    for key in assets:
        print(f"{key}: {assets[key]}")


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


def ask_to_proceed(message="Do you want to proceed (y/n): "):
    """
    Prompts the user with a yes/no question and returns the user's choice.

    Args:
        message (str, optional): The prompt message to display. Defaults to "Do you want to proceed (y/n): ".

    Returns:
        bool: True if the user enters 'y', False if the user enters 'n'.
    """
    print()
    while True:
        choice = input(message).lower()
        if choice in ["y", "n"]:
            return choice == "y"
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


if __name__ == "__main__":
    main()

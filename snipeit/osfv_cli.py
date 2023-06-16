#!/usr/bin/env python3

from rtectrl_api import RTE
import snipeit_api 
import argparse

# List used assets
def list_used_assets():
    all_assets = snipeit_api.get_all_assets()
    used_assets = [asset for asset in all_assets if asset['assigned_to'] is not None]

    if used_assets:
        for asset in used_assets:
            print_asset_details(asset)
    else:
        print('No used assets found.')

# List unused assets
def list_unused_assets():
    all_assets = snipeit_api.get_all_assets()
    unused_assets = [asset for asset in all_assets if asset['assigned_to'] is None]

    if unused_assets:
        for asset in unused_assets:
            print_asset_details(asset)
    else:
        print('No unused assets found.')

# List all assets
def list_all_assets():
    all_assets = snipeit_api.get_all_assets()

    if all_assets:
        for asset in all_assets:
            print_asset_details(asset)
    else:
        print('No assets found.')

# Print asset details as JSON with specific custom fields
def list_for_zabbix():
    all_assets = snipeit_api.get_all_assets()

    if all_assets:
        for asset in all_assets:
            print_asset_details_for_zabbix(asset)
    else:
        print('No assets found.')

# Print asset details including custom fields
def print_asset_details(asset):
    print(f'Asset Tag: {asset["asset_tag"]}, Asset ID: {asset["id"]}, Name: {asset["name"]}, Serial: {asset["serial"]}')

    custom_fields = asset.get('custom_fields', {})
    if custom_fields:
        for field_name, field_data in custom_fields.items():
            field_value = field_data.get('value')
            print(f'{field_name}: {field_value}')

    print()

# Print asset details formatted as an input for Zabbix import script
def print_asset_details_for_zabbix(asset):
    output = {}

    custom_fields = asset.get('custom_fields', {})
    if custom_fields:
        for field_name, field_data in custom_fields.items():
            if field_name in ["RTE IP", "Sonoff IP", "PiKVM IP"]:
                field_value = field_data.get('value')
                if field_value:
                    key = f'{asset["asset_tag"]}_{field_name}'.replace(' ', '_')
                    output[key] = field_value
                    print(f'{key}: {output[key]}')

def power_on(rte, args):
    rte.power_on(args.time)

def power_off(rte, args):
    rte.power_off(args.time)

def reset(rte, args):
    rte.reset(args.time)

def gpio_get(rte, args):
    state = rte.gpio_get(args.gpio_no)
    print(f"GPIO {args.gpio_no} state: {state}")

def gpio_set(rte, args):
    rte.gpio_set(args.gpio_no, args.state)
    print(f"GPIO {args.gpio_no} state set to {args.state}")

def relay_toggle(rte, args):
    rte.relay_toggle()
    state = rte.relay_get()
    print(f"Relay state toggled. New state: {state}")

def relay_set(rte, args):
    rte.relay_set(args.state)
    print(f"Relay state set to {args.state}")

def relay_get(rte, args):
    state = rte.relay_get()
    print(f"Relay state: {state}")

# Main function
def main():
    parser = argparse.ArgumentParser(description='Snipe-IT Asset Retrieval')

    subparsers = parser.add_subparsers(title='commands', dest='command', help='Command to execute')

    snipeit_parser = subparsers.add_parser('snipeit', help='Snipe-IT commands')
    rte_parser = subparsers.add_parser('rte', help='RTE commands')

    # Snipe-IT subcommands
    snipeit_subparsers = snipeit_parser.add_subparsers(title='subcommands', dest='snipeit_cmd',
                                                       help='Snipe-IT subcommands')

    list_used_parser = snipeit_subparsers.add_parser('list_used', help='List all already used assets')

    list_unused_parser = snipeit_subparsers.add_parser('list_unused', help='List all unused assets')

    list_all_parser = snipeit_subparsers.add_parser('list_all', help='List all assets')

    list_zabbix_parser = snipeit_subparsers.add_parser('list_for_zabbix',
                                                       help='List assets in a format suitable for Zabbix integration')

    check_out_parser = snipeit_subparsers.add_parser('check_out', help='Check out an asset by providing the Asset ID or RTE IP')
    check_out_group = check_out_parser.add_mutually_exclusive_group(required=True)
    check_out_group.add_argument('--asset_id', type=int, help='Asset ID')
    check_out_group.add_argument('--rte_ip', type=str, help='RTE IP')

    check_in_parser = snipeit_subparsers.add_parser('check_in', help='Check in an asset by providing the Asset ID or RTE IP')
    check_in_group = check_in_parser.add_mutually_exclusive_group(required=True)
    check_in_group.add_argument('--asset_id', type=int, help='Asset ID')
    check_in_group.add_argument('--rte_ip', type=str, help='RTE IP address')

    # RTE subcommands
    rte_parser.add_argument('--rte_ip', type=str, help='RTE IP address', required=True)
    rte_subparsers = rte_parser.add_subparsers(title='subcommands', dest='rte_cmd', help='RTE subcommands')
    rel_parser = rte_subparsers.add_parser('rel', help='Control RTE relay')
    gpio_parser = rte_subparsers.add_parser('gpio', help='Control RTE GPIO')
    pwr_parser = rte_subparsers.add_parser('pwr', help='Control DUT power via RTE')

    # Power subcommands
    pwr_subparsers = pwr_parser.add_subparsers(title="subcommands", dest="pwr_cmd")
    power_on_parser = pwr_subparsers.add_parser("on", help="Power on")
    power_on_parser.add_argument("--time", type=int, default=1, help="Power button press time in seconds (default: 1)")
    power_off_parser = pwr_subparsers.add_parser("off", help="Power off")
    power_off_parser.add_argument("--time", type=int, default=5, help="Power button press time in seconds (default: 5)")
    reset_parser = pwr_subparsers.add_parser("reset", help="Reset")
    reset_parser.add_argument("--time", type=int, default=1, help="Reset button press time in seconds (default: 1)")

    # GPIO subcommands
    gpio_subparsers = gpio_parser.add_subparsers(title="subcommands", dest="gpio_cmd")
    get_gpio_parser = gpio_subparsers.add_parser("get", help="Get GPIO state")
    get_gpio_parser.add_argument("gpio_no", type=int, help="GPIO number")
    set_gpio_parser = gpio_subparsers.add_parser("set", help="Set GPIO state")
    set_gpio_parser.add_argument("gpio_no", type=int, help="GPIO number")
    set_gpio_parser.add_argument("state", choices=["high", "low", "high-z"], help="GPIO state")

    # Relay subcommands
    rel_subparsers = rel_parser.add_subparsers(title="subcommands", dest="rel_cmd")
    tgl_rel_parser = rel_subparsers.add_parser("tgl", help="Toggle relay state")
    get_rel_parser = rel_subparsers.add_parser("get", help="Get relay state")
    set_rel_parser = rel_subparsers.add_parser("set", help="Set relay state")
    set_rel_parser.add_argument("state", choices=["high", "low",], help="Relay state")

    args = parser.parse_args()

    if args.command == 'snipeit':
        if args.snipeit_cmd == 'list_used':
            list_used_assets()
        elif args.snipeit_cmd == 'list_unused':
            list_unused_assets()
        elif args.snipeit_cmd == 'list_all':
            list_all_assets()
        elif args.snipeit_cmd == 'list_for_zabbix':
            list_for_zabbix()
        elif args.snipeit_cmd == 'check_out':
            if args.asset_id:
                snipeit_api.check_out_asset(args.asset_id)
            elif args.rte_ip:
                asset_id = snipeit_api.get_asset_id_by_rte_ip(args.rte_ip)
                if asset_id:
                    snipeit_api.check_out_asset(asset_id)
                else:
                    print(f'No asset found with RTE IP: {args.rte_ip}')
        elif args.snipeit_cmd == 'check_in':
            if args.asset_id:
                snipeit_api.check_in_asset(args.asset_id)
            elif args.rte_ip:
                asset_id = snipeit_api.get_asset_id_by_rte_ip(args.rte_ip)
                if asset_id:
                    snipeit_api.check_in_asset(asset_id)
                else:
                    print(f'No asset found with RTE IP: {args.rte_ip}')

    elif args.command == 'rte':
        rte = RTE(args.rte_ip)

        if args.rte_cmd == 'rel':
            # Handle RTE relay related commands
            if args.rel_cmd == "tgl":
                relay_toggle(rte, args)
            elif args.rel_cmd == "get":
                relay_get(rte, args)
            elif args.rel_cmd == "set":
                relay_set(rte, args)
        elif args.rte_cmd == 'gpio':
            # Handle RTE GPIO related commands
            if args.gpio_cmd == "get":
                gpio_get(rte, args)
            elif args.gpio_cmd == "set":
                gpio_set(rte, args)
        elif args.rte_cmd == 'pwr':
            # Handle RTE power related commands
            if args.pwr_cmd == "on":
                power_on(rte, args)
            elif args.pwr_cmd == "off":
                power_off(rte, args)
            elif args.pwr_cmd == "reset":
                reset(rte, args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3

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

# Main function
def main():
    parser = argparse.ArgumentParser(description='Snipe-IT Asset Retrieval')

    subparsers = parser.add_subparsers(title='commands', dest='command', help='Command to execute')

    list_used_parser = subparsers.add_parser('list_used', help='List all already used assets')

    list_unused_parser = subparsers.add_parser('list_unused', help='List all unused assets')

    list_all_parser = subparsers.add_parser('list_all', help='List all assets')

    list_zabbix_parser = subparsers.add_parser('list_for_zabbix', help='List assets in a format suitable for Zabbix integration')

    check_out_parser = subparsers.add_parser('check_out', help='Check out an asset by providing the Asset ID or RTE IP')
    check_out_group = check_out_parser.add_mutually_exclusive_group(required=True)
    check_out_group.add_argument('--asset_id', type=int, help='Asset ID')
    check_out_group.add_argument('--rte_ip', type=str, help='RTE IP')

    check_in_parser = subparsers.add_parser('check_in', help='Check in an asset by providing the Asset ID or RTE IP')
    check_in_group = check_in_parser.add_mutually_exclusive_group(required=True)
    check_in_group.add_argument('--asset_id', type=int, help='Asset ID')
    check_in_group.add_argument('--rte_ip', type=str, help='RTE IP')

    args = parser.parse_args()

    if args.command == 'list_used':
        list_used_assets()
    elif args.command == 'list_unused':
        list_unused_assets()
    elif args.command == 'list_all':
        list_all_assets()
    elif args.command == 'list_for_zabbix':
        list_for_zabbix()
    elif args.command == 'check_out':
        if args.asset_id:
            snipeit_api.check_out_asset(args.asset_id)
        elif args.rte_ip:
            # Use the RTE IP to find the asset ID and perform check out
            asset_id = snipeit_api.get_asset_id_by_rte_ip(args.rte_ip)
            if asset_id:
                snipeit_api.check_out_asset(asset_id)
            else:
                print(f'No asset found with RTE IP: {args.rte_ip}')
    elif args.command == 'check_in':
        if args.asset_id:
            snipeit_api.check_in_asset(args.asset_id)
        elif args.rte_ip:
            # Use the RTE IP to find the asset ID and perform check in
            asset_id = snipeit_api.get_asset_id_by_rte_ip(args.rte_ip)
            if asset_id:
                snipeit_api.check_in_asset(asset_id)
            else:
                print(f'No asset found with RTE IP: {args.rte_ip}')

if __name__ == '__main__':
    main()

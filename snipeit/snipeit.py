#!/usr/bin/env python3

import argparse
import requests
import yaml
import os
import sys

CONFIG_FILE_PATH = os.path.expanduser('~/.osfv/snipeit.yml')

# Retrieve API configuration from YAML file
def load_api_config():
    try:
        with open(CONFIG_FILE_PATH, 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f'Configuration file not found')
    except yaml.YAMLError as e:
        raise ValueError(f'Error parsing YAML: {e}')

    if config is None:
        raise ValueError(f'Empty configuration file')
        sys.exit(1)

    api_url = config.get('api_url')
    api_token = config.get('api_token')
    user_id = config.get('user_id')

    if not api_url or not api_token:
        raise ValueError('Incomplete API configuration in the YAML file')
    if not isinstance(user_id, int):
        raise ValueError(f'User ID configuration in the YAML file should be int: {user_id}')

    return api_url, api_token, user_id

try:
    # API endpoint and authentication token
    api_url, api_token, user_id = load_api_config()
except FileNotFoundError as e:
    print(f'Configuration file not found at {CONFIG_FILE_PATH}: {e}')
    sys.exit(1)
except ValueError as e:
    print(f'Please check the {CONFIG_FILE_PATH} file: {e}')
    sys.exit(1)

# Headers for API requests
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {api_token}'
}

# Retrieve all assets
def get_all_assets():
    page = 1
    all_assets = []

    while True:
        response = requests.get(f'{api_url}/hardware', headers=headers, params={'limit': 500, 'offset': (page - 1) * 500}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            all_assets.extend(data['rows'])
            if 'total_pages' not in data or data['total_pages'] <= page:
                break
            page += 1
        else:
            print(f'Error retrieving assets. Status code: {response.status_code}')
            print(response.json())
            break

    return all_assets

# List used assets
def list_used_assets():
    all_assets = get_all_assets()
    used_assets = [asset for asset in all_assets if asset['assigned_to'] is not None]

    if used_assets:
        for asset in used_assets:
            print_asset_details(asset)
    else:
        print('No used assets found.')

# List unused assets
def list_unused_assets():
    all_assets = get_all_assets()
    unused_assets = [asset for asset in all_assets if asset['assigned_to'] is None]

    if unused_assets:
        for asset in unused_assets:
            print_asset_details(asset)
    else:
        print('No unused assets found.')

# List all assets
def list_all_assets():
    all_assets = get_all_assets()

    if all_assets:
        for asset in all_assets:
            print_asset_details(asset)
    else:
        print('No assets found.')

# Print asset details as JSON with specific custom fields
def list_for_zabbix():
    all_assets = get_all_assets()

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

def get_asset_id_by_rte_ip(rte_ip):
    # Retrieve all assets
    all_assets = get_all_assets()

    # Search for asset with matching RTE IP
    for asset in all_assets:
        custom_fields = asset.get('custom_fields', {})
        if custom_fields:
            rte_ip_field = next((field_data['value'] for field_name, field_data in custom_fields.items() if field_name == 'RTE IP'), None)
            if rte_ip_field == rte_ip:
                return asset['id']

    # No asset found with matching RTE IP
    return None

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


# Check out an asset
def check_out_asset(asset_id):
    data = {
        'asset_id': asset_id,
        'assigned_user': user_id,
        'checkout_to_type': 'user'
    }
    response = requests.post(f'{api_url}/hardware/{asset_id}/checkout', headers=headers, json=data, timeout=10)

    if response.status_code == 200:
        print(f'Asset {asset_id} successfully checked out to {user_id} user.')
    else:
        print(f'Error checking out asset {asset_id} to user {user_id}. Status code: {response.status_code}')
        print(response.json())

# Check in an asset
def check_in_asset(asset_id):
    response = requests.post(f'{api_url}/hardware/{asset_id}/checkin', headers=headers, timeout=10)

    if response.status_code == 200:
        print(f'Asset {asset_id} successfully checked in.')
    else:
        print(f'Error checking in asset {asset_id}. Status code: {response.status_code}')
        print(response.json())

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
            check_out_asset(args.asset_id)
        elif args.rte_ip:
            # Use the RTE IP to find the asset ID and perform check out
            asset_id = get_asset_id_by_rte_ip(args.rte_ip)
            if asset_id:
                check_out_asset(asset_id)
            else:
                print(f'No asset found with RTE IP: {args.rte_ip}')
    elif args.command == 'check_in':
        if args.asset_id:
            check_in_asset(args.asset_id)
        elif args.rte_ip:
            # Use the RTE IP to find the asset ID and perform check in
            asset_id = get_asset_id_by_rte_ip(args.rte_ip)
            if asset_id:
                check_in_asset(asset_id)
            else:
                print(f'No asset found with RTE IP: {args.rte_ip}')

if __name__ == '__main__':
    main()

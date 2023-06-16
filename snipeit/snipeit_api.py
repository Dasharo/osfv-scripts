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

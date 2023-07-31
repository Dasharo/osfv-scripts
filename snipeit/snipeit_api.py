import requests
import yaml
import os
import sys
import string
import secrets
import unidecode
import json

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
    response_json = response.json()

    if response.status_code == 200 and response_json.get('status') != 'error':
        return True, response_json
    else:
        return False, response_json

# Check in an asset
def check_in_asset(asset_id):
    response = requests.post(f'{api_url}/hardware/{asset_id}/checkin', headers=headers, timeout=10)
    print(response)
    response_json = response.json()

    if response.status_code == 200 and response_json.get('status') != 'error':
        return True, response_json
    else:
        return False, response_json

def get_asset_model_name(asset_id):
    response = requests.get(f'{api_url}/hardware/{asset_id}', headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        model_name = data['model']['name']
    else:
        print(f'Error retrieving assets. Status code: {response.status_code}')
        print(response.json())
        model_name = None

    return model_name

def get_company_id(company_name):
    response = requests.get(f'{api_url}/companies', headers=headers, timeout=10)
    if response.status_code == 200:
        companies_data = response.json()
        for company in companies_data["rows"]:
            if company["name"] == company_name:
                return company["id"]
        return None
    else:
        print(f"Error retrieving companies. Status code: {response.status_code}")
        print(response.json())
        return None

def get_group_id(group_name):
    response = requests.get(f'{api_url}/groups', headers=headers, timeout=10)
    if response.status_code == 200:
        groups_data = response.json()
        for group in groups_data["rows"]:
            if group["name"] == group_name:
                return group["id"]
        return None
    else:
        print(f"Error retrieving user groups. Status code: {response.status_code}")
        print(response.json())
        return None

def generate_password(length=16):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password

def get_users():
    page = 1
    users = []

    while True:
        response = requests.get(f'{api_url}/users', headers=headers, params={'limit': 50, 'offset': (page - 1) * 50}, timeout=10)
        # print(response.json())
        if response.status_code == 200:
            data = response.json()
            users.extend(data['rows'])
            if 'total' not in data or data['total'] <= page:
                break
            page += 1
        else:
            print(f"Error retrieving users. Status code: {response.status_code}")
            print(response.json())
            break

        return users

def user_add(first_name, last_name, company_name):
    email = f"{unidecode.unidecode(first_name.lower())}.{unidecode.unidecode(last_name.lower())}@3mdeb.com"
    username = f"{first_name[0].lower()}{last_name.lower()}"
    password = generate_password()

    users = get_users()
    for user in users:
        if user["username"] == username:
            print(f"User with username '{username}' already exists.")
            return

    group_id = get_group_id("Users")
    if group_id is None:
        print("Group 'Users' not found in Snipe-IT.")
        return

    company_id = get_company_id(company_name)
    if company_id is None:
        print(f"Company {company_name} not found in Snipe-IT.")
        return

    data = {
        'first_name': first_name,
        'last_name': last_name,
        'username': username,
        'email': email,
        'password': password,
        'password_confirmation': password,
        'company_id': company_id ,
        'groups': group_id,
        'activated': True,
    }
    print(data)

    response = requests.post(f'{api_url}/users', headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        user_info = response.json()['payload']
        user_id = user_info["id"]
        print(f"User created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"User ID: {user_id}")
    else:
        print(f"Failed to create user. Status code: {response.status_code}")
        print(response.json())

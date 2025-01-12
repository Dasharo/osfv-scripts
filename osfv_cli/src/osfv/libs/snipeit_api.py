import os
import secrets
import string

import requests
import unidecode
import yaml


class SnipeIT:
    def __init__(self):
        snipeit_cfg = self.load_snipeit_config()
        self.cfg_api_url = snipeit_cfg["url"]
        self.cfg_api_token = snipeit_cfg["token"]
        self.cfg_user_id = snipeit_cfg["user_id"]
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.cfg_api_token}",
        }

    SNIPEIT_CONFIG_FILE_PATH = os.getenv(
        "SNIPEIT_CONFIG_FILE_PATH", os.path.expanduser("~/.osfv/snipeit.yml")
    )

    # Retrieve API configuration from YAML file
    def load_snipeit_config(self):
        try:
            with open(self.SNIPEIT_CONFIG_FILE_PATH, "r") as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Configuration file not found. Create one based on: https://github.com/Dasharo/osfv-scripts/tree/main/osfv_cli"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML: {e}")

        if config is None:
            raise ValueError(f"Empty configuration file")

        cfg = {}
        cfg["url"] = config.get("api_url")
        cfg["token"] = config.get("api_token")
        cfg["user_id"] = config.get("user_id")

        if not cfg["url"] or not ["cfg_token"]:
            raise ValueError("Incomplete API configuration in the YAML file")
        if not isinstance(cfg["user_id"], int):
            raise ValueError(
                f'User ID configuration in the YAML file should be int: {cfg["user_id"]}'
            )

        return cfg

    # Retrieve all assets
    def get_all_assets(self):
        page = 1
        all_assets = []

        while True:
            response = requests.get(
                f"{self.cfg_api_url}/hardware",
                headers=self.headers,
                params={"limit": 500, "offset": (page - 1) * 500},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                all_assets.extend(data["rows"])
                if "total_pages" not in data or data["total_pages"] <= page:
                    break
                page += 1
            else:
                print(
                    f"Error retrieving assets. Status code: {response.status_code}"
                )
                print(response.json())
                break

        return all_assets

    def get_asset_id_by_rte_ip(self, rte_ip):
        # Retrieve all assets
        all_assets = self.get_all_assets()

        # Search for asset with matching RTE IP
        for asset in all_assets:
            custom_fields = asset.get("custom_fields", {})
            if custom_fields:
                rte_ip_field = next(
                    (
                        field_data["value"]
                        for field_name, field_data in custom_fields.items()
                        if field_name == "RTE IP"
                    ),
                    None,
                )
                if rte_ip_field == rte_ip:
                    return asset["id"]

        # No asset found with matching RTE IP
        return None

    def get_asset_id_by_sonoff_ip(self, rte_ip):
        # Retrieve all assets
        all_assets = self.get_all_assets()

        # Search for asset with matching RTE IP
        for asset in all_assets:
            custom_fields = asset.get("custom_fields", {})
            if custom_fields:
                rte_ip_field = next(
                    (
                        field_data["value"]
                        for field_name, field_data in custom_fields.items()
                        if field_name == "Sonoff IP"
                    ),
                    None,
                )
                if rte_ip_field == rte_ip:
                    return asset["id"]

        # No asset found with matching RTE IP
        return None

    def get_sonoff_ip_by_rte_ip(self, rte_ip):
        # Retrieve all assets
        all_assets = self.get_all_assets()

        # Search for asset with matching RTE IP
        for asset in all_assets:
            custom_fields = asset.get("custom_fields", {})
            if custom_fields:
                rte_ip_field = next(
                    (
                        field_data["value"]
                        for field_name, field_data in custom_fields.items()
                        if field_name == "RTE IP"
                    ),
                    None,
                )
                if rte_ip_field == rte_ip:
                    if custom_fields["Sonoff IP"]:
                        return custom_fields["Sonoff IP"]["value"]

        # No asset found with matching RTE IP
        return None

    def get_pikvm_ip_by_rte_ip(self, rte_ip):
        # Retrieve all assets
        all_assets = self.get_all_assets()

        # Search for asset with matching RTE IP
        for asset in all_assets:
            custom_fields = asset.get("custom_fields", {})
            if custom_fields:
                rte_ip_field = next(
                    (
                        field_data["value"]
                        for field_name, field_data in custom_fields.items()
                        if field_name == "RTE IP"
                    ),
                    None,
                )
                if rte_ip_field == rte_ip:
                    if custom_fields["PiKVM IP"]:
                        return custom_fields["PiKVM IP"]["value"]

        # No asset found with matching PiKVM IP
        return None

    # Check out an asset
    def check_out_asset(self, asset_id):
        """
        Checks out an asset to the current user.

        This method attempts to check out the specified asset to the user identified by `self.cfg_user_id`.
        If the asset is already checked out to this user, the method will simply confirm this status.
        Otherwise, it will make an HTTP POST request to check out the asset.

        Parameters:
        asset_id (str): The unique identifier of the asset to be checked out.

        Returns:
        tuple:
            bool: Indicates if the checkout operation was initiated (True) or not (False).
            dict or None: The JSON response from the API if the checkout was initiated, otherwise None.
            bool: Indicates if the asset was already checked out to the current user (True) or not (False).

        Raises:
        requests.exceptions.RequestException: If the HTTP request to the API fails.
        """
        status, asset_data = self.get_asset(asset_id)

        if not status:
            return False, None, False

        # Simply pass if asset is already checked out to the caller
        if asset_data["assigned_to"]:
            assigned_to_id = asset_data["assigned_to"]["id"]
            if assigned_to_id == self.cfg_user_id:
                return True, None, True

        data = {
            "asset_id": asset_id,
            "assigned_user": self.cfg_user_id,
            "checkout_to_type": "user",
        }
        response = requests.post(
            f"{self.cfg_api_url}/hardware/{asset_id}/checkout",
            headers=self.headers,
            json=data,
            timeout=10,
        )
        response_json = response.json()

        if (
            response.status_code == 200
            and response_json.get("status") != "error"
        ):
            return True, response_json, False
        else:
            return False, response_json, False

    # Check in an asset
    def check_in_asset(self, asset_id):
        response = requests.post(
            f"{self.cfg_api_url}/hardware/{asset_id}/checkin",
            headers=self.headers,
            timeout=10,
        )
        response_json = response.json()

        if (
            response.status_code == 200
            and response_json.get("status") != "error"
        ):
            return True, response_json
        else:
            return False, response_json

    def get_asset(self, asset_id):
        response = requests.get(
            f"{self.cfg_api_url}/hardware/{asset_id}",
            headers=self.headers,
            timeout=10,
        )
        response_json = response.json()
        if (
            response.status_code == 200
            and response_json.get("status") != "error"
        ):
            return True, response_json
        else:
            return False, response_json

    def get_asset_model_name(self, asset_id):
        status, data = self.get_asset(asset_id)

        if not status:
            return False, data

        return True, data["model"]["name"]

    def get_company_id(self, company_name):
        response = requests.get(
            f"{self.cfg_api_url}/companies", headers=self.headers, timeout=10
        )
        if response.status_code == 200:
            companies_data = response.json()
            for company in companies_data["rows"]:
                if company["name"] == company_name:
                    return company["id"]
            return None
        else:
            print(
                f"Error retrieving companies. Status code: {response.status_code}"
            )
            print(response.json())
            return None

    def get_group_id(self, group_name):
        response = requests.get(
            f"{self.cfg_api_url}/groups", headers=self.headers, timeout=10
        )
        if response.status_code == 200:
            groups_data = response.json()
            for group in groups_data["rows"]:
                if group["name"] == group_name:
                    return group["id"]
            return None
        else:
            print(
                f"Error retrieving user groups. Status code: {response.status_code}"
            )
            print(response.json())
            return None

    def generate_password(self, length=16):
        characters = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(characters) for i in range(length))
        return password

    def get_users(self):
        page = 1
        users = []

        while True:
            response = requests.get(
                f"{self.cfg_api_url}/users",
                headers=self.headers,
                params={"limit": 50, "offset": (page - 1) * 50},
                timeout=10,
            )
            # print(response.json())
            if response.status_code == 200:
                data = response.json()
                users.extend(data["rows"])
                if "total" not in data or data["total"] <= page:
                    break
                page += 1
            else:
                print(
                    f"Error retrieving users. Status code: {response.status_code}"
                )
                print(response.json())
                break

            return users

    def get_user_id(self, username):
        users = self.get_users()
        if users:
            for user in users:
                if user["username"] == username:
                    return user["id"]
            return None

    def user_add(self, first_name, last_name, company_name):
        email = f"{unidecode.unidecode(first_name.lower())}.{unidecode.unidecode(last_name.lower())}@3mdeb.com"
        username = (
            f"{first_name[0].lower()}{unidecode.unidecode(last_name.lower())}"
        )
        password = self.generate_password()

        users = self.get_users()
        if users:
            for user in users:
                if user["username"] == username:
                    print(f"User with username '{username}' already exists.")
                    return

        group_id = self.get_group_id("Users")
        if group_id is None:
            print("Group 'Users' not found in Snipe-IT.")
            return

        company_id = self.get_company_id(company_name)
        if company_id is None:
            print(f"Company {company_name} not found in Snipe-IT.")
            return

        # For some reason, with our SnipeIT instance the group IT assignment does
        # not work and we still need to do this manually...
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "password": password,
            "password_confirmation": password,
            "company_id": company_id,
            "groups": group_id,
            "activated": True,
        }
        print(data)

        response = requests.post(
            f"{self.cfg_api_url}/users",
            headers=self.headers,
            json=data,
            timeout=10,
        )
        response_json = response.json()
        if (
            response.status_code == 200
            and response_json.get("status") != "error"
        ):
            user_info = response.json()["payload"]
            user_id = user_info["id"]
            print(f"User created successfully!")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print(f"User ID: {user_id}")
        else:
            print(
                f"Failed to create user. Status code: {response.status_code}"
            )
            print(response_json)

    def user_del(self, first_name, last_name):
        email = f"{unidecode.unidecode(first_name.lower())}.{unidecode.unidecode(last_name.lower())}@3mdeb.com"
        username = (
            f"{first_name[0].lower()}{unidecode.unidecode(last_name.lower())}"
        )

        user_id = self.get_user_id(username)
        if not user_id:
            print(f"Failed to find user with username: {username}")
            return

        response = requests.delete(
            f"{self.cfg_api_url}/users/{user_id}",
            headers=self.headers,
            timeout=10,
        )
        response_json = response.json()
        if (
            response.status_code == 200
            and response_json.get("status") != "error"
        ):
            print(f"User {username} deleted successfully!")
        else:
            print(
                f"Failed to delete user {username}. Status code: {response.status_code}"
            )
            print(response_json)

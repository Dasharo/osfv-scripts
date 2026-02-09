import os
import secrets
import string
import sys
import time

import requests
import unidecode
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SnipeIT:
    class DuplicatedIpException(Exception):
        def __init__(self, counts, field_name, expected_ip):
            # filling some data and composing an error message
            self.count = int(counts[field_name])
            self.field_name = field_name
            self.expected_ip = expected_ip
            self.message = (
                "FATAL: You are trying to access an asset with "
                + self.field_name
                + ": "
                + self.expected_ip
                + " which is not exclusive. Please check Snipe-IT data."
            )

            # disabling traceback, this is intentional failure.
            sys.tracebacklimit = 0
            super().__init__(self.message)

        def __str__(self):
            return self.message

    def __init__(self):
        snipeit_cfg = self.load_snipeit_config()
        self.cfg_api_url = snipeit_cfg["url"]
        self.cfg_api_token = snipeit_cfg["token"]
        self.cfg_user_id = snipeit_cfg["user_id"]
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.cfg_api_token}",
        }
        self.session = self._init_session()
        self.all_assets = None
        self.assets_cache = {}

    SNIPEIT_CONFIG_FILE_PATH = os.getenv(
        "SNIPEIT_CONFIG_FILE_PATH", os.path.expanduser("~/.osfv/snipeit.yml")
    )

    def _init_session(self):
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _request(
        self,
        method,
        url,
        params=None,
        data=None,
        json=None,
        headers=None,
        max_retries=3,
        timeout=10,
    ):
        delay = 2
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers or self.headers,
                    params=params,
                    data=data,
                    json=json,
                    timeout=timeout,
                )

                response_json = response.json()

                if (
                    response.status_code == 200
                    and response_json.get("status") != "error"
                ):
                    return True, response_json
                else:
                    return False, response_json

            except requests.exceptions.Timeout:
                print(
                    f"[Timeout] {method.upper()} {url} — retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay *= 2

            except requests.exceptions.RequestException as e:
                return False, {"error": str(e)}

        return False, {
            "error": f"{method.upper()} {url} failed after {max_retries} retries"
        }

    def _request_get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def _request_post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)

    def load_snipeit_config(self):
        """
        Loads the Snipe-IT API configuration from a YAML file.

        This method attempts to read and parse the YAML configuration file specified by `self.SNIPEIT_CONFIG_FILE_PATH`.
        It extracts the API URL, token, and user ID, performing validation to ensure required fields are present
        and correctly formatted.

        Args:
            None.

        Returns:
        dict: A dictionary containing the API configuration with the following keys:
            - "url" (str): The API base URL.
            - "token" (str): The API authentication token.
            - "user_id" (int): The user ID.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            ValueError: If the YAML file is empty, contains invalid YAML syntax, or has missing/incorrect fields.
        """
        try:
            with open(self.SNIPEIT_CONFIG_FILE_PATH, "r") as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found")
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
                f"User ID configuration in the YAML file should be int: "
                f'{cfg["user_id"]}'
            )

        return cfg

    def get_all_assets(self):
        """
        Retrieves all hardware assets from the Snipe-IT API.

        This method makes paginated requests to the Snipe-IT API to fetch all available hardware assets.
        It continues requesting data until all pages have been retrieved.

        Args:
            None.

        Returns:
            list: A list of dictionaries, where each dictionary represents an asset.
        """
        if self.all_assets is not None:
            return self.all_assets
        page = 1
        all_assets = []

        while True:
            success, data = self._request_get(
                f"{self.cfg_api_url}/hardware",
                params={"limit": 500, "offset": (page - 1) * 500},
            )
            if success:
                all_assets.extend(data["rows"])
                if "total_pages" not in data or data["total_pages"] <= page:
                    break
                page += 1
            else:
                print(f"Error retrieving assets: {data}")
                break
        self.all_assets = all_assets
        for asset in all_assets:
            self.assets_cache[asset["id"]] = (success, asset)
        return all_assets

    def __retieve_custom_field_value(self, custom_fields, expected_field_name):
        my_field = next(
            (
                field_data["value"]
                for field_name, field_data in custom_fields.items()
                if field_name == expected_field_name
            ),
            None,
        )
        if my_field:
            return my_field
        else:
            return None

    def __count_customField(
        self, custom_fields, counts, field_name, expected_ip
    ):
        my_field = self.__retieve_custom_field_value(custom_fields, field_name)

        if my_field:
            if my_field == expected_ip:
                counts[field_name] += 1
                if counts[field_name] > 1:
                    raise self.DuplicatedIpException(
                        counts, field_name, expected_ip
                    )
        return None

    # check by selected IP-fields (continue until second occurrence of any)
    def check_asset_for_ip_exclusivity(
        self, all_assets, ip=None, rte_ip=None, sonoff_ip=None, pikvm_ip=None
    ):
        # all IP-containing data fields
        occurence_counts = {
            "IP": 0,
            "RTE IP": 0,
            "Sonoff IP": 0,
            "PiKVM IP": 0,
        }
        for asset in all_assets:
            custom_fields = asset.get("custom_fields", {})
            if custom_fields:
                if ip:
                    self.__count_customField(
                        custom_fields, occurence_counts, "IP", ip
                    )
                if rte_ip:
                    self.__count_customField(
                        custom_fields, occurence_counts, "RTE IP", rte_ip
                    )
                if sonoff_ip:
                    self.__count_customField(
                        custom_fields, occurence_counts, "Sonoff IP", sonoff_ip
                    )
                if pikvm_ip:
                    self.__count_customField(
                        custom_fields, occurence_counts, "PiKVM IP", pikvm_ip
                    )
        return None

    # check by asset ID, on any non-empty IP field
    def check_asset_for_ip_exclusivity_by_id(self, asset_id):
        status, asset_data = self.get_asset(asset_id)
        if not status:
            return None

        custom_fields = asset_data.get("custom_fields", {})
        if custom_fields:
            ip = self.__retieve_custom_field_value(custom_fields, "IP")
            rte_ip = self.__retieve_custom_field_value(custom_fields, "RTE IP")
            sonoff_ip = self.__retieve_custom_field_value(
                custom_fields, "Sonoff IP"
            )
            pikvm_ip = self.__retieve_custom_field_value(
                custom_fields, "PiKVM IP"
            )

            self.check_asset_for_ip_exclusivity(
                self.get_all_assets(), ip, rte_ip, sonoff_ip, pikvm_ip
            )
        return None

    def get_asset_id_by_rte_ip(self, rte_ip):
        """
        Retrieves the asset ID associated with a given RTE IP.

        This method first checks for duplicate occurrences of the provided RTE IP among all assets.
        Then, it searches for the asset that contains the specified RTE IP in its custom fields.
        If a matching asset is found, it performs a secondary exclusivity check by asset ID before returning the asset's ID.

        Aegs:
            rte_ip (str): The RTE IP address to search for.

        Returns:
            str or None: The asset ID if found, otherwise None.

        Raises:
            DuplicatedIpException: If the RTE IP appears more than once across all assets.
        """
        all_assets = self.get_all_assets()
        self.check_asset_for_ip_exclusivity(
            all_assets, None, rte_ip, None, None
        )

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
                    # re-run exclusivty check by asset ID
                    self.check_asset_for_ip_exclusivity_by_id(asset["id"])
                    return asset["id"]

        # No asset found with matching RTE IP
        return None

    def get_asset_id_by_sonoff_ip(self, rte_ip):
        """
        Retrieves the asset ID associated with a given Sonoff IP.

        Firstly, this method checks for duplicate occurrences of the
        provided Sonoff IP among all assets.
        Then, it searches for the asset that contains the specified
        Sonoff IP in its custom fields.
        If a matching asset is found, it performs a secondary exclusivity
        check by asset ID before returning the asset's ID.

        Parameters:
        sonoff_ip (str): The Sonoff IP address to search for.

        Returns:
        str or None: The asset ID if found, otherwise None.

        Raises:
        DuplicatedIpException: If the Sonoff IP appears more than once across all assets.
        """
        # Retrieve all assets with matching rte_ip.
        all_assets = self.get_all_assets()
        self.check_asset_for_ip_exclusivity(
            all_assets, None, None, rte_ip, None
        )

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
                    # re-run exclusivty check by asset ID
                    self.check_asset_for_ip_exclusivity_by_id(asset["id"])
                    return asset["id"]

        # No asset found with a specified RTE IP
        return None

    def get_sonoff_ip_by_rte_ip(self, rte_ip):
        # Retrieve all assets with matching rte_ip.
        all_assets = self.get_all_assets()
        self.check_asset_for_ip_exclusivity(
            all_assets, None, rte_ip, None, None
        )

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
        # Retrieve all assets with matching rte_ip.
        all_assets = self.get_all_assets()
        self.check_asset_for_ip_exclusivity(
            all_assets, None, rte_ip, None, None
        )

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

    def check_out_asset(self, asset_id):
        """
        Checks out an asset to the current user.

        This method attempts to check out the specified asset to the user
        identified by `self.cfg_user_id`. If the asset is already checked out
        to this user, the method will simply confirm this status.
        Otherwise, it will make an HTTP POST request to check out the asset.

        Args:
            asset_id (str): The unique identifier of the asset to be checked out.

        Returns:
            tuple:
                bool: Indicates if the checkout operation was initiated (True) or not (False).
                dict or None: The JSON response from the API if the checkout was initiated, otherwise None.
                bool: Indicates if the asset was already checked out to the current user (True) or not (False).
            requests.exceptions.RequestException: If the HTTP request to the API fails.
        """
        self.check_asset_for_ip_exclusivity_by_id(asset_id)

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
        success, response = self._request_post(
            f"{self.cfg_api_url}/hardware/{asset_id}/checkout",
            json=data,
        )
        return success, response, False

    def check_in_asset(self, asset_id):
        """
        Check in an asset.

        Args:
            asset_id (str): The unique identifier of the asset to be checked out.

        Returns:
            success status with a response object from server.
        """
        return self._request_post(
            f"{self.cfg_api_url}/hardware/{asset_id}/checkin"
        )

    def get_asset(self, asset_id):
        """
        Retrieve asset information from a hardware configuration API by sending
        a GET request with a specified asset_id.

        Args:
            asset_id (str): The unique identifier of the asset to be checked out.

        Returns:
            success status with a response object from server.
        """
        if asset_id not in self.assets_cache:
            self.assets_cache[asset_id] = self._request_get(
                f"{self.cfg_api_url}/hardware/{asset_id}"
            )
        return self.assets_cache[asset_id]

    def get_asset_model_name(self, asset_id):
        """
        Retrieve the model name of an asset by calling the get_asset method.

        Args:
            asset_id (str): The unique identifier of the asset.

        Returns:
            tuple: A tuple where the first element is a boolean indicating the success (True/False),
                and the second element is either the model name or an error message.
        """
        status, data = self.get_asset(asset_id)

        if not status:
            return False, data

        return True, data["model"]["name"]

    def get_company_id(self, company_name):
        """
        Retrieve the ID of a company by sending a GET request to fetch all companies from the API.

        Args:
            company_name (str): The name of the company for which to retrieve the ID.

        Returns:
            str or None: The company ID if found, otherwise None if the company
            doesn't exist or if there was an error retrieving the data.
        """
        success, data = self._request_get(f"{self.cfg_api_url}/companies")
        if success:
            for company in data["rows"]:
                if company["name"] == company_name:
                    return company["id"]
            return None
        else:
            print(f"Error retrieving companies: {data}")
            return None

    def get_group_id(self, group_name):
        """
        Retrieve the ID of a user group by sending a GET request to fetch all groups from the API.

        Args:
            group_name (str): The name of the group for which to retrieve the ID.

        Returns:
            str or None: The group ID if found, otherwise None if the group doesn't exist
            or if there was an error retrieving the data.
        """
        success, data = self._request_get(f"{self.cfg_api_url}/groups")
        if success:
            for group in data["rows"]:
                if group["name"] == group_name:
                    return group["id"]
            return None
        else:
            print(f"Error retrieving user groups: {data}")
            return None

    def generate_password(self, length=16):
        """
        Generate a random password.

        Args:
            length (int, optional): length of a new password, default value is 16.

        Returns:
            a string with new password.
        """
        characters = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(characters) for i in range(length))
        return password

    def get_users(self):
        """
        Retrieve a list of users from the API, fetching results in paginated chunks of 50 users per request.

        Args:
            None.

        Returns:
            The list of all the users.
        """
        page = 1
        users = []

        while True:
            success, data = self._request_get(
                f"{self.cfg_api_url}/users",
                params={"limit": 50, "offset": (page - 1) * 50},
            )
            if success:
                users.extend(data["rows"])
                if "total" not in data or data["total"] <= page:
                    break
                page += 1
            else:
                print(f"Error retrieving users: {data}")
                break

            return users

    def get_user_id(self, username):
        """
        Retrieve the ID of a user by calling get_users() and searching for a user with the specified username.

        Args:
            username (str): The username of the user to search for.

        Returns:
            str or None: The user ID if the user is found, otherwise None if the user doesn't exist.
        """
        users = self.get_users()
        if users:
            for user in users:
                if user["username"] == username:
                    return user["id"]
            return None

    def user_add(self, first_name, last_name, company_name):
        """
        Create a new user by generating an email, username,
        and password based on the provided arguments.

        Args:
            first_name (str): The first name of the new user.
            last_name (str): The last name of the new user.
            company_name (str): The name of the company assigned to the user.

        Returns:
            None.
        """
        email = (
            f"{unidecode.unidecode(first_name.lower())}."
            f"{unidecode.unidecode(last_name.lower())}@3mdeb.com"
        )
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

        # For some reason, with our SnipeIT instance the group IT assignment
        # does not work and we still need to do this manually...
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

        success, response = self._request_post(
            f"{self.cfg_api_url}/users",
            json=data,
        )
        if success:
            user_info = response["payload"]
            user_id = user_info["id"]
            print(f"User created successfully!")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print(f"User ID: {user_id}")
        else:
            print(f"Failed to create user: {data}")

    def user_del(self, first_name, last_name):
        """
        Delete a user with matching first_name and last_name.

        Args:
            first_name (str): The first name of the deleted user.
            last_name (str): The last name of the deleted user.

        Returns:
            None.
        """
        email = (
            f"{unidecode.unidecode(first_name.lower())}."
            f"{unidecode.unidecode(last_name.lower())}@3mdeb.com"
        )
        username = (
            f"{first_name[0].lower()}{unidecode.unidecode(last_name.lower())}"
        )

        user_id = self.get_user_id(username)
        if not user_id:
            print(f"Failed to find user with username: {username}")
            return

        success, response = self._request(
            "DELETE", f"{self.cfg_api_url}/users/{user_id}"
        )
        if success:
            print(f"User {username} deleted successfully!")
        else:
            print(f"Failed to delete user {username}: {response}")

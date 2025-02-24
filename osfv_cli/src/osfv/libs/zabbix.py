#!/usr/bin/env python3

import json
import os

import requests
import yaml


class Zabbix:
    ZABBIX_CONFIG_FILE_PATH = os.path.expanduser("~/.osfv/zabbix.yml")

    def __init__(self):
        with open(self.ZABBIX_CONFIG_FILE_PATH, "r") as config_file:
            config = yaml.safe_load(config_file)
            self.api_url = config["api_url"]
            self.api_username = config["username"]
            self.api_password = config["password"]

            self.auth_token = self.authenticate()

            return

    def get_headers(self):
        """
        Get headers form the server.

        Args:
            None.

        Returns:
            a dictionary containing the headers for an HTTP request.
        """
        return {"Content-Type": "application/json"}

    def authenticate(self):
        """
        Authenticate and retrieve the authentication token.

        Args:
            None.

        Returns:
            a response object form server.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": self.api_username,
                "password": self.api_password,
            },
            "id": 1,
            "auth": None,
        }
        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        result = response.json()
        if "result" in result:
            return result["result"]
        elif "error" in result:
            error_message = result["error"]["message"]
            raise ValueError(
                f"Zabbix API authentication failed: {error_message}"
            )
        else:
            raise ValueError("Invalid response from Zabbix API authentication")

    def get_all_hosts_json(self):
        """
        Retrieve a list of hosts.

        Args:
            None.

        Returns:
            a response object form server.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "selectInterfaces": ["ip"],
                "output": ["hostid", "host"],
            },
            "id": 1,
            "auth": self.auth_token,
        }

        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        return response.json()

    def get_all_hosts(self):
        """
        Retrieve all hosts from the API.

        Args:
            None.

        Returns:
            a response object form server.
        """
        return self.format_hosts(self.get_all_hosts_json())

    def format_hosts(self, hosts):
        """
        Convert a JSON object containing host information to a dictionary mapping host names to their IP addresses.

        Args:
            hosts (dict): A JSON object containing a list of hosts with their details.

        Returns:
            dict: A dictionary where keys are host names and values are their respective IP addresses.
        """
        result = {}
        for host in hosts["result"]:
            result[host["host"]] = host["interfaces"][0]["ip"]

        return result

    def add_host(self, host_name, ip_address):
        """
        Add a new host with ICMP template.

        Args:
            host_name: The name of the host to be identified in the sever.
            ip_address: IP address to be assigned to the host.

        Returns:
            str: a response object form server with added hostid.

        Rises:
            Failed to add host: If there is an error in response.
            Invalid response from Zabbix API host creation: If there is an unspecified error.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {"output": ["hostid"], "filter": {"host": [host_name]}},
            "auth": self.auth_token,
            "id": 1,
        }
        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        result = response.json()
        if "result" in result and len(result["result"]) > 0:
            print(
                f"A host with name '{host_name}' already exists. Skipping host "
                f"creation."
            )
            return result["result"][0]["hostid"]

        payload["params"]["filter"] = {"ip": [ip_address]}
        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        result = response.json()
        if "result" in result and len(result["result"]) > 0:
            print(
                f"A host with IP address '{ip_address}' already exists. "
                f"Skipping host creation."
            )
            return result["result"][0]["hostid"]

        # Host doesn't exist, proceed with host creation
        payload = {
            "jsonrpc": "2.0",
            "method": "host.create",
            "params": {
                "host": host_name,
                "interfaces": [
                    {
                        "type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": ip_address,
                        "dns": "",
                        "port": "10050",
                    }
                ],
                "groups": [{"groupid": "1"}],
                "templates": [{"templateid": "10186"}],  # ICMP template ID
            },
            "auth": self.auth_token,
            "id": 1,
        }
        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        result = response.json()
        if "result" in result and "hostids" in result["result"]:
            return result["result"]["hostids"][0]
        elif "error" in result:
            error_message = result["error"]["message"]
            raise ValueError(f"Failed to add host: {error_message}")
        else:
            raise ValueError("Invalid response from Zabbix API host creation")

    def get_host_id_by_name(self, host_name):
        """
        Retrieve the host ID for a given host name.

        Args:
            host_name: The name of the host to be identified in the sever.

        Returns:
            a response object form server with added hostid.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {"output": ["hostid"], "filter": {"host": [host_name]}},
            "auth": self.auth_token,
            "id": 1,
        }

        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        data = response.json()

        # Extract the hostid
        return data["result"][0]["hostid"] if data.get("result") else None

    def get_host_interface_id(self, host_name):
        """
        Retrieve the interface ID of a given host by querying the API.

        Args:
            host_name: The name of the host to be identified in the sever.

        Returns:
            a response object form server with interfaces and interfaceid.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid"],
                "filter": {"host": [host_name]},
                "selectInterfaces": ["interfaceid"],
            },
            "auth": self.auth_token,
            "id": 1,
        }

        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        data = response.json()

        return (
            data["result"][0]["interfaces"][0]["interfaceid"]
            if data.get("result")
            else None
        )

    def update_host_ip(self, host_name, new_ip):
        """
        Update IP of the host.

        Args:
            host_name: The name of the host to be identified in the sever.
            new_ip: New IP address to be assigned to the host.

        Returns:
            a response object form server.
        """
        interface_id = self.get_host_interface_id(host_name)
        if not interface_id:
            return {"error": "Could not find the host or its interface."}

        payload = {
            "jsonrpc": "2.0",
            "method": "hostinterface.update",
            "params": {"interfaceid": interface_id, "ip": new_ip},
            "auth": self.auth_token,
            "id": 2,
        }

        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        return response.json()

    def remove_host_by_name(self, host_name):
        """
        Remove the selected host.

        Args:
            host_name: The name of the removed host.

        Returns:
            a response object form server.
        """
        host_id = self.get_host_id_by_name(host_name)
        if not host_id:
            return {"error": "Could not find the host."}

        payload = {
            "jsonrpc": "2.0",
            "method": "host.delete",
            "params": [host_id],
            "auth": self.auth_token,
            "id": 2,
        }

        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        return response.json()

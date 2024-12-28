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
        return {"Content-Type": "application/json"}

    # Function to authenticate and retrieve the authentication token
    def authenticate(self):
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
        return self.format_hosts(self.get_all_hosts_json())

    # converts hosts json to dictionary
    def format_hosts(self, hosts):
        result = {}
        for host in hosts["result"]:
            result[host["host"]] = host["interfaces"][0]["ip"]

        return result

    # Function to add a new host with ICMP template
    def add_host(self, host_name, ip_address):
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
                f"A host with name '{host_name}' already exists. Skipping host creation."
            )
            return result["result"][0]["hostid"]

        payload["params"]["filter"] = {"ip": [ip_address]}
        response = requests.post(
            self.api_url, headers=self.get_headers(), data=json.dumps(payload)
        )
        result = response.json()
        if "result" in result and len(result["result"]) > 0:
            print(
                f"A host with IP address '{ip_address}' already exists. Skipping host creation."
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

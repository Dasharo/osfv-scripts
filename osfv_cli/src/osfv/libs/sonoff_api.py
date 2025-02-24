import requests


class SonoffDevice:
    def __init__(self, sonoff_ip):
        self.sonoff_ip = sonoff_ip

    def _get_request(self, endpoint):
        """
        Send a GET request to a specified endpoint on a Sonoff device using its IP address.

        Args:
            endpoint (str): The endpoint to which the GET request should be sent.

        Returns:
            dict: The parsed JSON response from the Sonoff device.
        """
        url = f"http://{self.sonoff_ip}{endpoint}"
        response = requests.request("GET", url)
        # Raise an exception for non-2xx responses (4xx and 5xx status codes)
        response.raise_for_status()
        return response.json()

    def _post_request(self, endpoint):
        """
        Send a POST request to a specified endpoint on a Sonoff device using its IP address.

        Args:
            endpoint (str): The endpoint to which the POST request should be sent.

        Returns:
            int: The HTTP status code of the response.
        """
        url = f"http://{self.sonoff_ip}{endpoint}"
        response = requests.request("POST", url)
        # Raise an exception for non-2xx responses (4xx and 5xx status codes)
        response.raise_for_status()
        # Sonoff POST requests return no data
        return response.status_code

    def turn_on(self):
        """
        Send a POST request to a Sonoff device to turn it on.

        Args:
            None.

        Returns:
            int: HTTP status code of the response.
        """
        endpoint = "/cm?cmnd=Power%20On"
        return self._post_request(endpoint)

    def turn_off(self):
        """
        Send a POST request to a Sonoff device to turn it off.

        Args:
            None.

        Returns:
            int: HTTP status code of the response.
        """
        endpoint = "/cm?cmnd=Power%20off"
        return self._post_request(endpoint)

    def get_state(self):
        """
        Send a GET request to a Sonoff device to retrieve its power state.

        Args:
            None.

        Returns:
            str: The current power state of the Sonoff device, typically "ON" or "OFF".
        """
        endpoint = "/cm?cmnd=Power"
        response = self._get_request(endpoint)
        return response.get("POWER")

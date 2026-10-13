import logging
import time

import requests

# Healthy Sonoffs answer within ~0.3 s (worst seen ~3.5 s), ones on a poor
# Wi-Fi link within ~12 s. Without a timeout a response stalled mid-body
# blocks forever, so bound every request and retry; the commands are
# idempotent.
SONOFF_TIMEOUT = (5, 15)  # (connect, read) in seconds
SONOFF_RETRIES = 3
SONOFF_RETRY_DELAY = 2


class SonoffDevice:
    def __init__(self, sonoff_ip):
        self.sonoff_ip = sonoff_ip

    def _request(self, method, endpoint):
        """
        Send a request to a specified endpoint on a Sonoff device, retrying
        on connection errors and timeouts.

        Args:
            method (str): HTTP method to use.
            endpoint (str): The endpoint to which the request should be sent.

        Returns:
            Response: The HTTP response object.
        """
        url = f"http://{self.sonoff_ip}{endpoint}"
        for attempt in range(1, SONOFF_RETRIES + 1):
            try:
                response = requests.request(
                    method, url, timeout=SONOFF_TIMEOUT
                )
                # Raise an exception for 4xx and 5xx status codes
                response.raise_for_status()
                return response
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as e:
                logging.warning(
                    f"Sonoff {method} {url} failed "
                    f"(attempt {attempt}/{SONOFF_RETRIES}): {e}"
                )
                if attempt == SONOFF_RETRIES:
                    raise
                time.sleep(SONOFF_RETRY_DELAY)

    def _get_request(self, endpoint):
        """
        Send a GET request to a specified endpoint on a Sonoff device using its IP address.

        Args:
            endpoint (str): The endpoint to which the GET request should be sent.

        Returns:
            dict: The parsed JSON response from the Sonoff device.
        """
        return self._request("GET", endpoint).json()

    def _post_request(self, endpoint):
        """
        Send a POST request to a specified endpoint on a Sonoff device using its IP address.

        Args:
            endpoint (str): The endpoint to which the POST request should be sent.

        Returns:
            int: The HTTP status code of the response.
        """
        # Sonoff POST requests return no data
        return self._request("POST", endpoint).status_code

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

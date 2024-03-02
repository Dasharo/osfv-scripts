import requests


class SonoffDevice:
    def __init__(self, sonoff_ip):
        self.sonoff_ip = sonoff_ip

    def _get_request(self, endpoint):
        url = f"http://{self.sonoff_ip}{endpoint}"
        response = requests.request("GET", url)
        # Raise an exception for non-2xx responses (4xx and 5xx status codes)
        response.raise_for_status()
        return response.json()

    def _post_request(self, endpoint):
        url = f"http://{self.sonoff_ip}{endpoint}"
        response = requests.request("POST", url)
        # Raise an exception for non-2xx responses (4xx and 5xx status codes)
        response.raise_for_status()
        # Sonoff POST requests return no data
        return response.status_code

    def turn_on(self):
        endpoint = "/cm?cmnd=Power%20On"
        return self._post_request(endpoint)

    def turn_off(self):
        endpoint = "/cm?cmnd=Power%20Off"
        return self._post_request(endpoint)

    def get_state(self):
        endpoint = "/cm?cmnd=Power"
        response = self._get_request(endpoint)
        return response.get("POWER")

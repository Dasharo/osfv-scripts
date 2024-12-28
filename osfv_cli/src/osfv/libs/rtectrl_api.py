import requests

BASE_URL_TEMPLATE = "http://{rte_ip}:8000/api/v1"

headers = {"Content-Type": "application/json", "Accept": "application/json"}


class rtectrl:
    """
    A class to control and interact with GPIO pins on an RTE device using its REST API.

    Attributes:
        GPIO_MIN (int): Minimum valid GPIO number (0).
        GPIO_MAX (int): Maximum valid GPIO number (19).
    """

    GPIO_MIN = 0
    GPIO_MAX = 19

    def __init__(self, rte_ip):
        """
        Initializes the `rtectrl` instance.

        Args:
            rte_ip (str): IP address of the RTE device.
        """
        self.rte_ip
        self.rte_ip = rte_ip

    def gpio_list(self):
        """
        Retrieves a list of all GPIO configurations from the RTE device.

        Returns:
            list: A JSON response containing details of all GPIO configurations.
        """
        response = self._get_request(f"/gpio").json()
        return response

    def gpio_get(self, gpio_no):
        """
        Retrieves the state of a specific GPIO pin.

        Args:
            gpio_no (int): GPIO pin number to retrieve the state for.

        Returns:
            str: State of the GPIO pin. For pins 1-12: "low" or "high-z".
                 For pins 0, 13-19: "high" or "low".

        Raises:
            GPIOWrongNumberError: If the GPIO number is outside the valid range.
        """
        if not self.GPIO_MIN <= gpio_no <= self.GPIO_MAX:
            raise GPIOWrongNumberError("Wrong GPIO number")

        # GPIOS:
        #   0 - relay (regular GPIO)
        #   1 - 12 - OC GPIOs
        #   13 - 19 - regular GPIOs
        state = self._get_request(f"/gpio/{gpio_no}").json()["state"] % 2
        if 1 <= gpio_no <= 12:
            if state == 1:
                state_str = "low"
            else:
                state_str = "high-z"
        if 13 <= gpio_no <= 19 or gpio_no == 0:
            if state == 1:
                state_str = "high"
            else:
                state_str = "low"

        return state_str

    def gpio_set(self, gpio_no, state_str, sleep=0):
        """
        Sets the state of a specific GPIO pin.

        Args:
            gpio_no (int): GPIO pin number to set the state for.
            state_str (str): Desired state for the GPIO pin.
                             For pins 1-12: "low" or "high-z".
                             For pins 0, 13-19: "high" or "low".
            sleep (int, optional): Duration in seconds for which to maintain the state. Default is 0.

        Raises:
            GPIOWrongNumberError: If the GPIO number is outside the valid range.
            GPIOWrongStateError: If an invalid GPIO state is provided.
            RuntimeError: If the API request fails to set the GPIO state.
        """
        if not self.GPIO_MIN <= gpio_no <= self.GPIO_MAX:
            raise GPIOWrongNumberError("Wrong GPIO number")

        # GPIOS:
        #   0 - relay (regular GPIO)
        #   1 - 12 - OC GPIOs
        #   13 - 19 - regular GPIOs
        if 1 <= gpio_no <= 12:
            if state_str == "low":
                state = 1
            elif state_str == "high-z":
                state = 0
            else:
                raise GPIOWrongStateError("Wrong GPIO state")
        if 13 <= gpio_no <= 19 or gpio_no == 0:
            if state_str == "high":
                state = 1
            elif state_str == "low":
                state = 0
            else:
                raise GPIOWrongStateError("Wrong GPIO state")

        try:
            message = {"state": state, "direction": "out", "time": sleep}
            response = self._patch_request(f"/gpio/{gpio_no}", message)
            if response.status_code != 200:
                raise RuntimeError("Failed to set GPIO state")
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ProtocolError,
        ) as e:
            print(f"Failed while setting gpio {e}")

    def _get_request(self, endpoint):
        """
        Sends a GET request to the specified API endpoint.

        Args:
            endpoint (str): API endpoint to send the GET request to.

        Returns:
            Response: The HTTP response object.

        Raises:
            HTTPError: If the response contains an HTTP error status code.
        """
        url = BASE_URL_TEMPLATE.format(rte_ip=self.rte_ip)
        response = requests.get(f"{url}{endpoint}", headers=headers)
        response.raise_for_status()
        return response

    def _patch_request(self, endpoint, data):
        """
        Sends a PATCH request to the specified API endpoint with the provided data.

        Args:
            endpoint (str): API endpoint to send the PATCH request to.
            data (dict): Data to include in the PATCH request body.

        Returns:
            Response: The HTTP response object.

        Raises:
            HTTPError: If the response contains an HTTP error status code.
        """
        url = BASE_URL_TEMPLATE.format(rte_ip=self.rte_ip)
        response = requests.patch(
            f"{url}{endpoint}", json=data, headers=headers
        )
        response.raise_for_status()
        return response


class GPIOWrongNumberError(Exception):
    """Raised when an invalid GPIO number is provided."""

    pass


class GPIOWrongStateError(Exception):
    """Raised when an invalid GPIO state is provided."""

    pass

import requests

BASE_URL_TEMPLATE = "http://{rte_ip}:8000/api/v1"

headers = {"Content-Type": "application/json", "Accept": "application/json"}

class rtectrl:
    GPIO_MIN = 0
    GPIO_MAX = 19

    def __init__(self, rte_ip):
        self.rte_ip = rte_ip
        self.rte_power

    def gpio_list(self):
        response = self._get_request(f"/gpio").json()
        return response

    def gpio_get(self, gpio_no):
        if not self.GPIO_MIN <= gpio_no <= self.GPIO_MAX:
            raise GPIOWrongNumberError("Wrong GPIO number")

        # GPIOS:
        #   0 - relay
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
        if not self.GPIO_MIN <= gpio_no <= self.GPIO_MAX:
            raise GPIOWrongNumberError("Wrong GPIO number")

        # GPIOS:
        #   0 - relay
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

        message = {"state": state, "direction": "out", "time": sleep}
        response = self._patch_request(f"/gpio/{gpio_no}", message)
        if response.status_code != 200:
            raise RuntimeError("Failed to set GPIO state")

    def _get_request(self, endpoint):
        url = BASE_URL_TEMPLATE.format(rte_ip=self.rte_ip)
        response = requests.get(f"{url}{endpoint}", headers=headers)
        response.raise_for_status()
        return response

    def _patch_request(self, endpoint, data):
        url = BASE_URL_TEMPLATE.format(rte_ip=self.rte_ip)
        response = requests.patch(f"{url}{endpoint}", json=data, headers=headers)
        response.raise_for_status()
        return response

class GPIOWrongNumberError(Exception):
    pass

class GPIOWrongStateError(Exception):
    pass

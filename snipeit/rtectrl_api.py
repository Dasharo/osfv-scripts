import requests
import time

BASE_URL_TEMPLATE = "http://{rte_ip}:8000/api/v1"

GPIO_MIN = 0
GPIO_MAX = 19

GPIO_SPI_ON = 1
GPIO_SPI_VOLTAGE = 2
GPIO_SPI_VCC = 3

GPIO_RELAY = 0
GPIO_RESET = 8
GPIO_POWER = 9

headers = {"Content-Type": "application/json", "Accept": "application/json"}


class RTE:
    def __init__(self, rte_ip):
        self.rte_ip = rte_ip

    def gpio_get(self, gpio_no):
        if not GPIO_MIN <= gpio_no <= GPIO_MAX:
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
        if not GPIO_MIN <= gpio_no <= GPIO_MAX:
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

    def power_on(self, sleep=1):
        self.gpio_set(GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def power_off(self, sleep=5):
        self.gpio_set(GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def reset(self, sleep=1):
        self.gpio_set(GPIO_RESET, "low", sleep)
        time.sleep(sleep)

    def relay_get(self):
        return self.gpio_get(GPIO_RELAY) 

    def relay_set(self, state):
        self.gpio_set(GPIO_RELAY, state)

    def relay_toggle(self):
        state_str = self.relay_get()
        if state_str == "low":
            new_state_str = "high"
        else:
            new_state_str = "low"
        self.relay_set(new_state_str)

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

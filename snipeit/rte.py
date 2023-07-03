from rtectrl_api import rtectrl 
import time

class RTE(rtectrl):
    GPIO_SPI_ON = 1
    GPIO_SPI_VOLTAGE = 2
    GPIO_SPI_VCC = 3
    
    GPIO_RELAY = 0
    GPIO_RESET = 8
    GPIO_POWER = 9

    def __init__(self, rte_ip):
        self.rte_ip = rte_ip

    def power_on(self, sleep=1):
        self.gpio_set(self.GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def power_off(self, sleep=5):
        self.gpio_set(self.GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def reset(self, sleep=1):
        self.gpio_set(self.GPIO_RESET, "low", sleep)
        time.sleep(sleep)

    def relay_get(self):
        return self.gpio_get(self.GPIO_RELAY) 

    def relay_set(self, state):
        self.gpio_set(self.GPIO_RELAY, state)

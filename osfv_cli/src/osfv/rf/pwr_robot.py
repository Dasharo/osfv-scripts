import os
import sys
import time

from robot.api.deco import keyword


# Power controller for all devices
class PowerController:
    def __init__(self, rte_ip):
        self.rte_ip = rte_ip
        self.default_power_switch = "relay"
        # Include getting other variables here, reading config
        # Sonoff IP and sonoff device
        # Relay can be done via this

    # Set desired power state to Enabled
    @keyword(types=None)
    def power_on(self):

        self.rte.relay_set(state)
        state = self.rte.relay_get()
        robot.api.logger.info(f"Relay state set to {state}")
        return state


    # Set desired power state to Disabled
    def power_off(self):

    # Complete full power cycle, desired power state Enabled
    def power_cycle(self):

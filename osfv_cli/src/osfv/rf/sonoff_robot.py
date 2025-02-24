import requests
import robot.api.logger
from osfv.libs.sonoff_api import SonoffDevice
from robot.api.deco import keyword


class Sonoff:
    def __init__(self, sonoff_ip):
        self.sonoff = SonoffDevice(sonoff_ip)

    @keyword(types=None)
    def sonoff_on(self):
        """
        Attempt to turn on the Sonoff relay and log the response.
        If an error occurs, it logs the failure and the error message.
        """
        robot.api.logger.info("Turning on Sonoff relay...")
        try:
            response = self.sonoff.turn_on()
            robot.api.logger.info(response)
        except requests.exceptions.RequestException as e:
            robot.api.logger.info(
                f"Failed to turn on Sonoff relay. Error: {e}"
            )

    @keyword(types=None)
    def sonoff_off(self):
        """
        Attempt to turn off the Sonoff relay and log the response.
        If an error occurs, it logs the failure and the error message.
        """
        robot.api.logger.info("Turning off Sonoff relay...")
        try:
            response = self.sonoff.turn_off()
            robot.api.logger.info(response)
        except requests.exceptions.RequestException as e:
            robot.api.logger.info(
                f"Failed to turn off Sonoff relay. Error: {e}"
            )

    @keyword(types=None)
    def sonoff_get(self):
        """
        Retrieve and logs the current state of the Sonoff relay.
        If an error occurs, it log the failure and the error message.
        """
        state = None
        robot.api.logger.info("Getting Sonoff relay state...")
        try:
            state = self.sonoff.get_state()
            robot.api.logger.info(f"Sonoff relay state: {state}")
        except requests.exceptions.RequestException as e:
            robot.api.logger.info(
                f"Failed to get Sonoff relay state. Error: {e}"
            )
        return state

    @keyword(types=None)
    def sonoff_tgl(self):
        """
        Toggle the state of the Sonoff relay based on its current state, either turning it on or off,
        and log the action. If an error occurs, it log the failure and error message.
        """
        robot.api.logger.info("Toggling Sonoff relay state...")
        try:
            response = self.sonoff.get_state()
            current_state = response.get("state")

            if current_state == "ON":
                response = self.sonoff.turn_off()
                robot.api.logger.info("Sonoff relay state toggled off.")
            elif current_state == "OFF":
                response = self.sonoff.turn_on()
                robot.api.logger.info("Sonoff relay state toggled on.")
            else:
                robot.api.logger.info(
                    f"Unexpected Sonoff relay state: {current_state}"
                )
        except requests.exceptions.RequestException as e:
            robot.api.logger.info(
                f"Failed to toggle Sonoff relay state. Error: {e}"
            )

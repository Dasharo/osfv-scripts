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
        Attempt to turn on the Sonoff power switch and log the response.

        Logs the success or failure of the operation. If an error occurs,
        the failure and error message are logged.

        Args:
            None

        Returns:
            None
        """
        robot.api.logger.info("Turning on Sonoff power switch...")
        try:
            response = self.sonoff.turn_on()
            robot.api.logger.info(response)
        except requests.exceptions.RequestException as e:
            robot.api.logger.info(
                f"Failed to turn on Sonoff power switch. Error: {e}"
            )

    @keyword(types=None)
    def sonoff_off(self):
        """
        Attempt to turn off the Sonoff power switch and log the response.

        Logs the success or failure of the operation. If an error occurs,
        the failure and error message are logged.

        Args:
            None

        Returns:
            None
        """
        robot.api.logger.info("Turning off Sonoff power switch...")
        try:
            response = self.sonoff.turn_off()
            robot.api.logger.info(response)
        except requests.exceptions.RequestException as e:
            robot.api.logger.info(
                f"Failed to turn off Sonoff power switch. Error: {e}"
            )

    @keyword(types=None)
    def sonoff_get(self):
        """
        Retrieve and logs the current state of the Sonoff power switch.
        If an error occurs, it logs the failure and the error message.

        Args:
            None

        Returns:
            str: The current state of the Sonoff power switch (e.g., "low", "high").
        """
        state = None
        robot.api.logger.info("Getting Sonoff power switch state...")
        try:
            state = self.sonoff.get_state()
            robot.api.logger.info(f"Sonoff power switch state: {state}")
        except requests.exceptions.RequestException as e:
            robot.api.logger.info(
                f"Failed to get Sonoff power switch state. Error: {e}"
            )
        return state

    @keyword(types=None)
    def sonoff_tgl(self):
        """
        Toggle the state of the Sonoff power switch based on its current state, either turning it on or off,
        and log the action. If an error occurs, it logs the failure and error message.

        Args:Attempt to turn on the Sonoff power switch and log the response.
            None

        Returns:
            None
        """
        robot.api.logger.info("Toggling Sonoff power switch state...")
        try:
            response = self.sonoff.get_state()
            current_state = response.get("state")

            if current_state == "ON":
                response = self.sonoff.turn_off()
                robot.api.logger.info("Sonoff power switch state toggled off.")
            elif current_state == "OFF":
                response = self.sonoff.turn_on()
                robot.api.logger.info("Sonoff power switch state toggled on.")
            else:
                robot.api.logger.info(
                    f"Unexpected Sonoff power switch state: {current_state}"
                )
        except requests.exceptions.RequestException as e:
            robot.api.logger.info(
                f"Failed to toggle Sonoff power switch state. Error: {e}"
            )

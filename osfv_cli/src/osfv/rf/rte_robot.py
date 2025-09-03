import osfv.libs.utils as utils
import robot.api.logger
from osfv.libs.models import UnsupportedDUTModel
from osfv.libs.rte import RTE
from osfv.libs.snipeit_api import SnipeIT
from osfv.libs.sonoff_api import SonoffDevice
from robot.api.deco import keyword, library

model_dict = {
    "odroid-h4-plus": "H4-PLUS",
    "odroid-h4-ultra": "H4-ULTRA",
    "gigabyte-mz33-ar1": "MZ33-AR1 Rev. 3",
    "minnowboard-turbot": "MinnowBoard Turbot B41",
    "msi-pro-z690-a-ddr4": "MSI PRO Z690-A DDR4",
    "msi-pro-z690-a-wifi-ddr4": "MSI PRO Z690-A DDR4",
    "msi-pro-z690-a-ddr5": "MSI PRO Z690-A DDR5",
    "msi-pro-z790-p-ddr5": "MSI PRO Z790-P DDR5",
    "novacustom-ns50mu": "NS50MU",
    "novacustom-v540tu": "V540TU",
    "novacustom-v540tnd": "V540TND",
    "novacustom-v560tu": "V560TU",
    "novacustom-v560tnd": "V560TND",
    "novacustom-v560tne": "V560TNE",
    "novacustom-nuc_box-125H": "NUC BOX-125H",
    "novacustom-nuc_box-155H": "NUC BOX-155H",
    "pcengines-apu2": "APU2",
    "pcengines-apu3": "APU3",
    "pcengines-apu4": "APU4",
    "pcengines-apu6": "APU6",
    "pcengines-apu2-seabios": "APU2",
    "pcengines-apu3-seabios": "APU3",
    "pcengines-apu4-seabios": "APU4",
    "pcengines-apu6-seabios": "APU6",
    "protectli-v1210": "V1210",
    "protectli-v1410": "V1410",
    "protectli-v1610": "V1610",
    "protectli-vp2410": "VP2410",
    "protectli-vp2420": "VP2420",
    "protectli-vp2430": "VP2430",
    "protectli-vp2440": "VP2440",
    "protectli-vp3210": "VP3210",
    "protectli-vp3230": "VP3230",
    "protectli-vp4630": "VP4630",
    "protectli-vp4650": "VP4650",
    "protectli-vp4670": "VP4670",
    "protectli-vp6650": "VP6650",
    "protectli-vp6670": "VP6670",
}


@library(scope="GLOBAL")
class RobotRTE:
    def __init__(self, rte_ip, snipeit: bool, sonoff_ip=None, config=None):
        self.rte_ip = rte_ip
        if snipeit:
            self.snipeit_api = SnipeIT()
            asset_id = self.snipeit_api.get_asset_id_by_rte_ip(rte_ip)
            status, dut_model_name = self.snipeit_api.get_asset_model_name(
                asset_id
            )
            if status:
                robot.api.logger.info(
                    f"DUT model retrieved from snipeit: {dut_model_name}"
                )
            else:
                raise AssertionError(
                    f"Failed to retrieve model name from Snipe-IT. Check again "
                    f"arguments, or try providing model manually."
                )
            self.sonoff, self.sonoff_ip = utils.init_sonoff(
                sonoff_ip, self.rte_ip, self.snipeit_api
            )
            # bug: https://github.com/Dasharo/open-source-firmware-validation/issues/646
            # Some RTE-less platforms still need to use this class to
            # instantiate sonoff and/or snipeit.
            # Ideally these would go to a separate class.
            if self.rte_ip != "0.0.0.0":
                self.rte = RTE(rte_ip, dut_model_name, self.sonoff)
        else:
            self.sonoff, self.sonoff_ip = utils.init_sonoff(
                sonoff_ip, self.rte_ip
            )
            # bug: as above
            if self.rte_ip != "0.0.0.0":
                self.rte = RTE(
                    rte_ip, self.cli_model_from_osfv(config), self.sonoff
                )

    def cli_model_from_osfv(self, osfv_model):
        """
        Check if the .yml file with the name matching osfv_model exists
        in the src/osfv/models/ directory.

        Args:
            osfv_model (str): The model name.

        Returns:
            str: The corresponding osfv_cli model name.

        Raises:
            TypeError: If the osfv_model argument is None.
            UnsupportedDUTModel: If the provided osfv_model has no counterpart in osfv_cli.
        """
        if not osfv_model:
            raise TypeError(f"Expected a value for 'config', but got None")
        cli_model = model_dict.get(osfv_model)
        if not cli_model:
            raise UnsupportedDUTModel(
                f"The {osfv_model} model has no counterpart in osfv_cli"
            )
        return cli_model

    @keyword(types=None)
    def rte_flash_read(self, fw_file):
        """
        Reads DUT flash chip content into the specified ``fw_file`` path.

        Args:
            fw_file (str): The file path where the flash content will be saved.

        Returns:
            int: The result code from the flash_read method of the rte object.
        """
        robot.api.logger.info(f"Reading from flash...")
        rc = self.rte.flash_read(fw_file)
        robot.api.logger.info(f"Read flash content saved to {fw_file}")
        return rc

    @keyword(types=None)
    def rte_flash_write(self, fw_file, bios=False):
        """
        Writes file from ``fw_file`` path into DUT flash chip.

        Args:
            fw_file (str): The file path containing the firmware to be written to the flash chip.
            bios (bool, optional): Whether to write the BIOS (default is False).

        Returns:
            int: The result code from the flash_write method of the rte object.
        """
        robot.api.logger.info(f"Writing {fw_file} to flash...")
        rc = self.rte.flash_write(fw_file, bios)
        if rc == 0:
            robot.api.logger.info(f"Flash written successfully")
        else:
            robot.api.logger.info(f"Flash write failed with code {rc}")
        return rc

    @keyword(types=None)
    def rte_flash_probe(self):
        """
        Probe the flash chip of the DUT.

        Args:
            None.

        Returns:
            int: The result code from the flash_probe method of the rte object.
        """
        robot.api.logger.info(f"Probing flash...")
        rc = self.rte.flash_probe()
        return rc

    @keyword(types=None)
    def rte_flash_erase(self):
        """
        Erase the flash chip of the DUT.

        Args:
            None.

        Returns:
            int: The result code from the flash_erase method of the rte object.
        """
        robot.api.logger.info(f"Erasing DUT flash...")
        rc = self.rte.flash_erase()
        robot.api.logger.info(f"Flash erased")
        return rc

    @keyword(types=None)
    def rte_relay_toggle(self):
        """
        Toggle the relay state between "low" and "high" on the DUT and log the new state.

        Args:
            None.

        Returns:
            None.
        """
        state_str = self.rte.relay_get()
        if state_str == "low":
            new_state_str = "high"
        else:
            new_state_str = "low"
        self.rte.relay_set(new_state_str)
        state = self.rte.relay_get()
        robot.api.logger.info(f"Relay state toggled. New state: {state}")

    @keyword(types=None)
    def rte_relay_set(self, state):
        """
        Set the relay to the specified state and log the new state.

        Args:
            state (str): The desired relay state ("low" or "high").

        Returns:
            str: The current state of the relay after the operation.
        """
        self.rte.relay_set(state)
        state = self.rte.relay_get()
        robot.api.logger.info(f"Relay state set to {state}")
        return state

    @keyword(types=None)
    def rte_relay_get(self):
        """
        Get the current state of the relay and log it.

        Returns:
            str: The current state of the relay ("low" or "high").
        """
        state = self.rte.relay_get()
        robot.api.logger.info(f"Relay state: {state}")
        return state

    @keyword(types=None)
    def rte_power_on(self, time=1):
        """
        Press the power button for a specified amount of time passed in argument.

        Args:
            time (int, optional): The duration in seconds to press the power button on the DUT.
            Default is 1 second.

        Returns:
            None
        """
        robot.api.logger.info(f"Powering on...")
        self.rte.power_on(time)

    @keyword(types=None)
    def rte_power_off(self, time=6):
        """
        Press the power button for a specified amount of time passed in argument.
        Keeping the power button pressed for at least 4 seconds causes
        a forced shutdown of the DUT.

        Args:
            time: The duration in seconds to power off the DUT. Default is 6 seconds.

        Returns:
            None
        """
        robot.api.logger.info(f"Powering off...")
        self.rte.power_off(time)

    @keyword(types=None)
    def rte_reset(self, time=1):
        """
        Press the reset button on the DUT for a specified amount of time and log the action.

        Args:
            time: The duration in seconds to press the reset button. Default is 1 second.

        Returns:
            None
        """
        robot.api.logger.info(f"Pressing reset button...")
        self.rte.reset(time)

    @keyword(types=None)
    def rte_psu_on(self):
        """
        Turn the power supply on for the DUT and log the action.

        Args:
            None

        Returns:
            None
        """
        robot.api.logger.info(f"Enabling power supply...")
        self.rte.psu_on()

    @keyword(types=None)
    def rte_psu_off(self):
        """
        Turn the power supply off for the DUT and log the action.

        Args:
            None

        Returns:
            None
        """
        robot.api.logger.info(f"Disabling power supply...")
        self.rte.psu_off()

    @keyword(types=None)
    def rte_psu_get(self):
        """
        Get the current state of the power supply for the DUT.

        Args:
            None

        Returns:
            The state of the power supply (e.g., True or False).
        """
        return self.rte.psu_get()

    @keyword(types=None)
    def rte_clear_cmos(self):
        robot.api.logger.info(f"Clearing CMOS...")
        self.rte.reset_cmos()

    @keyword(types=None)
    def rte_gpio_get(self, gpio_no):
        """
        Get the state of a specified GPIO pin.

        Args:
            gpio_no (int): The GPIO pin number to check.

        Returns:
            str: The state of the GPIO pin.
        """
        state = self.rte.gpio_get(int(gpio_no))
        robot.api.logger.info(f"GPIO {gpio_no} state: {state}")
        return state

    @keyword(types=None)
    def rte_gpio_set(self, gpio_no, state):
        """
        Set the state of a specified GPIO pin.

        Args:
            gpio_no (int): The GPIO pin number to set.
            state (str): The state to set the GPIO pin to (e.g., "high" or "low").

        Returns:
            None
        """
        self.rte.gpio_set(int(gpio_no), state)
        state = self.rte.gpio_get(int(gpio_no))
        robot.api.logger.info(f"GPIO {gpio_no} state set to {state}")

    @keyword(types=None)
    def rte_check_power_led(self):
        state = self.rte.gpio_get(RTE.GPIO_PWR_LED)
        polarity = self.dut_data.get("pwr_led", {}).get("polarity")
        if polarity and polarity == "active low":
            if state == "high":
                state = "low"
            else:
                state = "high"

        robot.api.logger.info(
            f"Power LED state: {'ON' if state == 'high' else 'OFF'}"
        )
        return state

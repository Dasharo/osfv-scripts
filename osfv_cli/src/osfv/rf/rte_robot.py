import osfv.libs.utils as utils
import robot.api.logger
from osfv.libs.rte import RTE, UnsupportedDUTModel
from osfv.libs.snipeit_api import SnipeIT
from osfv.libs.sonoff_api import SonoffDevice
from robot.api.deco import keyword

model_dict = {
    "odroid-h4-plus": "H4-PLUS",
    "minnowboard-turbot": "MinnowBoard Turbot B41",
    "msi-pro-z690-a-ddr4": "MSI PRO Z690-A DDR4",
    "msi-pro-z690-a-wifi-ddr4": "MSI PRO Z690-A DDR4",
    "msi-pro-z690-a-ddr5": "MSI PRO Z690-A DDR5",
    "pcengines-apu2": "APU2",
    "pcengines-apu3": "APU3",
    "pcengines-apu4": "APU4",
    "pcengines-apu6": "APU6",
    "protectli-v1210": "V1210",
    "protectli-v1410": "V1410",
    "protectli-v1610": "V1610",
    "protectli-vp2410": "VP2410",
    "protectli-vp2420": "VP2420",
    "protectli-vp2430": "VP2430",
    "protectli-vp3230": "VP3230",
    "protectli-vp4630": "VP4630",
    "protectli-vp4650": "VP4650",
    "protectli-vp4670": "VP4670",
    "protectli-vp6650": "VP6650",
    "protectli-vp6670": "VP6670",
}


class RobotRTE:
    def __init__(self, rte_ip, snipeit: bool, sonoff_ip=None, config=None):
        self.rte_ip = rte_ip
        if snipeit:
            self.snipeit_api = SnipeIT()
            asset_id = self.snipeit_api.get_asset_id_by_rte_ip(rte_ip)
            status, dut_model_name = self.snipeit_api.get_asset_model_name(asset_id)
            if status:
                robot.api.logger.info(
                    f"DUT model retrieved from snipeit: {dut_model_name}"
                )
            else:
                raise AssertionError(
                    f"Failed to retrieve model name from Snipe-IT. Check again arguments, or try providing model manually."
                )
            self.sonoff, self.sonoff_ip = utils.init_sonoff(
                sonoff_ip, self.rte_ip, self.snipeit_api
            )
            self.rte = RTE(rte_ip, dut_model_name, self.sonoff)
        else:
            self.sonoff, self.sonoff_ip = utils.init_sonoff(sonoff_ip, self.rte_ip)
            self.rte = RTE(rte_ip, self.cli_model_from_osfv(config), self.sonoff)

    def cli_model_from_osfv(self, osfv_model):
        """
        Get osfv_cli model name from OSFV repo config name
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
        """Reads DUT flash chip content into ``fw_file``  path"""
        robot.api.logger.info(f"Reading from flash...")
        rc = self.rte.flash_read(fw_file)
        robot.api.logger.info(f"Read flash content saved to {fw_file}")
        return rc

    @keyword(types=None)
    def rte_flash_write(self, fw_file, bios=False):
        """Writes file from ``fw_file`` path into DUT flash chip"""
        robot.api.logger.info(f"Writing {fw_file} to flash...")
        rc = self.rte.flash_write(fw_file, bios)
        if rc == 0:
            robot.api.logger.info(f"Flash written successfully")
        else:
            robot.api.logger.info(f"Flash write failed with code {rc}")
        return rc

    @keyword(types=None)
    def rte_flash_probe(self):
        robot.api.logger.info(f"Probing flash...")
        rc = self.rte.flash_probe()
        return rc

    @keyword(types=None)
    def rte_flash_erase(self):
        robot.api.logger.info(f"Erasing DUT flash...")
        rc = self.rte.flash_erase()
        robot.api.logger.info(f"Flash erased")
        return rc

    @keyword(types=None)
    def rte_relay_toggle(self):
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
        self.rte.relay_set(state)
        state = self.rte.relay_get()
        robot.api.logger.info(f"Relay state set to {state}")
        return state

    @keyword(types=None)
    def rte_relay_get(self):
        state = self.rte.relay_get()
        robot.api.logger.info(f"Relay state: {state}")
        return state

    @keyword(types=None)
    def rte_power_on(self, time=1):
        robot.api.logger.info(f"Powering on...")
        self.rte.power_on(time)

    @keyword(types=None)
    def rte_power_off(self, time=6):
        robot.api.logger.info(f"Powering off...")
        self.rte.power_off(time)

    @keyword(types=None)
    def rte_reset(self, time=1):
        robot.api.logger.info(f"Pressing reset button...")
        self.rte.reset(time)

    @keyword(types=None)
    def rte_gpio_get(self, gpio_no):
        state = self.rte.gpio_get(int(gpio_no))
        robot.api.logger.info(f"GPIO {gpio_no} state: {state}")
        return state

    @keyword(types=None)
    def rte_gpio_set(self, gpio_no, state):
        self.rte.gpio_set(int(gpio_no), state)
        state = self.rte.gpio_get(int(gpio_no))
        robot.api.logger.info(f"GPIO {gpio_no} state set to {state}")

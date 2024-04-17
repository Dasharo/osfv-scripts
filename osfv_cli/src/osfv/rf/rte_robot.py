import robot.api.logger
from robot.api.deco import keyword
from osfv.libs.rte import RTE
from osfv.libs.snipeit_api import SnipeIT


class RobotRTE:
    def __init__(self, rte_ip):
        snipeit_api = SnipeIT()
        asset_id = snipeit_api.get_asset_id_by_rte_ip(rte_ip)
        status, dut_model_name = snipeit_api.get_asset_model_name(asset_id)
        if status:
            robot.api.logger.info(f"DUT model retrieved from snipeit: {dut_model_name}")
        else:
            raise AssertionError(
                f"Failed to retrieve model name from Snipe-IT. Check again arguments, or try providing model manually."
            )
        self.rte = RTE(rte_ip, dut_model_name, snipeit_api)

    @keyword(types=None)
    def rte_flash_read(self, fw_file):
        """Reads DUT flash chip content into ``fw_file``  path
        """
        robot.api.logger.info(f"Reading from flash...")
        self.rte.flash_read(fw_file)
        robot.api.logger.info(f"Read flash content saved to {fw_file}")

    @keyword(types=None)
    def rte_flash_write(self, fw_file):
        """Writes file from ``fw_file`` path into DUT flash chip
        """
        robot.api.logger.info(f"Writing {fw_file} to flash...")
        self.rte.flash_write(fw_file)
        robot.api.logger.info(f"Flash written")

    @keyword(types=None)
    def rte_flash_probe(self):
        robot.api.logger.info(f"Probing flash...")
        self.rte.flash_probe()
    
    @keyword(types=None)
    def rte_flash_erase(self):
        robot.api.logger.info(f"Erasing DUT flash...")
        self.rte.flash_erase()
        robot.api.logger.info(f"Flash erased")

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

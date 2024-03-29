import robot.api.logger
from rte import RTE
from snipeit_api import SnipeIT


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

    def flash_read(self, fw_file):
        robot.api.logger.info(f"Reading from flash...")
        self.rte.flash_read(fw_file)
        robot.api.logger.info(f"Read flash content saved to {fw_file}")

    def flash_write(self, fw_file):
        robot.api.logger.info(f"Writing {fw_file} to flash...")
        self.rte.flash_write(fw_file)
        robot.api.logger.info(f"Flash written")

import robot.api.logger
import snipeit_api


def snipeit_checkout(rte_ip):
    asset_id = snipeit_api.get_asset_id_by_rte_ip(rte_ip)
    success, data = snipeit_api.check_out_asset(asset_id)
    if success:
        robot.api.logger.info(f"Asset {asset_id} successfully checked out.")
        return data
    else:
        raise AssertionError(
            f"Error checking out asset {asset_id}. Response data: {data}"
        )


def snipeit_checkin(rte_ip):
    asset_id = snipeit_api.get_asset_id_by_rte_ip(rte_ip)
    success, data = snipeit_api.check_in_asset(asset_id)
    if success:
        robot.api.logger.info(f"Asset {asset_id} successfully checked in.")
        return data
    else:
        raise AssertionError(
            f"Error checking in asset {asset_id}. Response data: {data}"
        )

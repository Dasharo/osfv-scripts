import robot.api.logger
from osfv.libs.snipeit_api import SnipeIT

snipeit_api = SnipeIT()


def snipeit_checkout(rte_ip):
    """
    Check out an asset by its rte_ip.
    Args:
        rte_ip (str): The IP address of the RTE device connected to a DUT.

    Returns:
        Information that the asset has already been checked out.

    Raises:
        AssertionError: If the check-out process fails.
    """
    asset_id = snipeit_api.get_asset_id_by_rte_ip(rte_ip)
    success, data, already_checked_out = snipeit_api.check_out_asset(asset_id)
    if success:
        robot.api.logger.info(f"Asset {asset_id} successfully checked out.")
        return already_checked_out
    else:
        raise AssertionError(
            f"Error checking out asset {asset_id}. Response data: {data}"
        )


def snipeit_checkin(rte_ip):
    """
    Check in an asset by its rte_ip.

    Args:
        rte_ip (str): The IP address of the RTE device connected to a DUT.

    Returns:
        data: The response data from the Snipe-IT API after checking in the asset.

    Raises:
        AssertionError: If the check-in process fails.
    """
    asset_id = snipeit_api.get_asset_id_by_rte_ip(rte_ip)
    success, data = snipeit_api.check_in_asset(asset_id)
    if success:
        robot.api.logger.info(f"Asset {asset_id} successfully checked in.")
        return data
    else:
        raise AssertionError(
            f"Error checking in asset {asset_id}. Response data: {data}"
        )


def snipeit_get_sonoff_ip(rte_ip):
    """
    Retrieve the Sonoff IP address associated with a given rte_ip.

    Args:
        rte_ip (str): The IP address of the RTE device connected to a DUT.

    Returns:
        str: The Sonoff IP address associated with the given RTE IP.
    """
    return snipeit_api.get_sonoff_ip_by_rte_ip(rte_ip)


def snipeit_get_pikvm_ip(rte_ip):
    """
    Retrieve the PiKVM IP address associated with a given rte_ip.

    Args:
        rte_ip (str): The IP address of the RTE device connected to a DUT.

    Returns:
        str: The PiKVM IP address associated with the given RTE IP.
    """
    return snipeit_api.get_pikvm_ip_by_rte_ip(rte_ip)


def snipeit_get_asset_model(rte_ip):
    """
    Retrieve the model name of an asset by its rte_ip.

    Args:
        rte_ip (str): The IP address of the RTE device connected to a DUT.

    Returns:
         str: The model name of the asset connected to RTE if retrieval is successful.

    Raises:
        AssertionError: If the model name cannot be retrieved.
    """
    asset_id = snipeit_api.get_asset_id_by_rte_ip(rte_ip)
    success, data = snipeit_api.get_asset_model_name(asset_id)
    if success:
        robot.api.logger.info(f"Asset {asset_id} model is: {data} in.")
        return data
    else:
        raise AssertionError(
            f"Error getting model name of asset: {asset_id}. "
            f"Response data: {data}"
        )

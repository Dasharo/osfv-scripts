import os

from osfv.libs.flash_image import FlashImage
from osfv.libs.sonoff_api import SonoffDevice


def init_sonoff(init_sonoff_ip, rte_ip, snipeit_api=None):
    """
    Initialize a Sonoff device instance. It either uses the provided `init_sonoff_ip` directly,
    or fetches the Sonoff device IP based on the `rte_ip` from the `snipeit_api`.

    Args:
        init_sonoff_ip (str): The Sonoff device IP to initialize with.
        rte_ip (str): The RTE device IP used to retrieve the Sonoff IP if `snipeit_api` is provided.
        snipeit_api (object, optional): An instance of the Snipe-IT API used to fetch Sonoff IP
                                        based on the RTE IP. Defaults to None.

    Returns:
        tuple: A tuple containing the Sonoff device instance and its IP address.
            - sonoff (SonoffDevice): The Sonoff device instance initialized with the Sonoff IP.
            - sonoff_ip (str): The IP address of the Sonoff device.
    """
    sonoff_ip = ""
    sonoff = None
    if not snipeit_api:
        sonoff_ip = init_sonoff_ip
    else:
        sonoff_ip = snipeit_api.get_sonoff_ip_by_rte_ip(rte_ip)
    sonoff = SonoffDevice(sonoff_ip)
    return sonoff, sonoff_ip


def check_flash_image_regions(
    rom, dry_run=False, verbose=False, regions=["me"]
):
    """
    Use osfv.libs.flash_image library to verify existence of given regions
    and data content of them (if described memory area is not filled with single
    byte value).

    Args:
    rom (str): Dasharo flash image file path.
    dry_run (bool): Enforce positive exit status, but error messages are still
                    displayed.
    regions ([str]): Each region string from this list is verified with
                     FlashImage.check_region() method.

    Returns: True in case of FlashImage exit status 0 or False otherwise.
    """

    flash_image = FlashImage()

    if verbose:
        flash_image.set_verbosity(1)

    print(f"Verifying flash image completeness of {rom} ...")
    flash_image.load_image_file(rom)

    for check_region_name in regions:
        check_region_index = flash_image.get_region_index(check_region_name)
        if check_region_index == None:
            continue
        flash_image.check_region(check_region_index, check_region_name)

    if dry_run:
        flash_image.set_exit_code(0)

    if flash_image.get_exit_code() != 0:
        print("ME check failed.")
        return False
    else:
        print("OK")
        return True

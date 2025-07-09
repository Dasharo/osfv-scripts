import os

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


def check_flash_image_regions(rom, dry_run=False, regions=["me"]):
    """
    Call ../osfv_mecheck/mecheck.py program to verify existence of given regions
    and data content of them (if described memory area is not filled with single
    byte value).

    Args:
    rom (str): Dasharo flash image file path.
    dry_run (bool): Append "-x" option to enforce positive command status, but
                    error messages are still displayed.
    regions ([str]): Each region string from this list is added to command line
                     with "-c" option.

    Returns: True in case of command return code 0 or False otherwise.
    """
    command_line = f"../osfv_mecheck/mecheck.py {rom}"
    for region in regions:
        command_line += f" -c {region}"
    if dry_run:
        command_line += " -x"
    print(f"Verifying flash image completeness of {rom} ...")
    return_code = os.system(command_line)
    if return_code != 0:
        ("mecheck.py failed.")
        return False
    else:
        print("OK")
        return True

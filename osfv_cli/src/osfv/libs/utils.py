from osfv.libs.sonoff_api import SonoffDevice


def init_sonoff(init_sonoff_ip, rte_ip, snipeit_api=None):
    """
    Initialize a Sonoff device instance. It either uses the build in init_sonoff_ip
    directly or fetches the Sonoff device IP based on the rte_ip from the snipeit_api.

    Returns:
        a tuple with sonoff and sonoff_ip strings.
    """
    sonoff_ip = ""
    sonoff = None
    if not snipeit_api:
        sonoff_ip = init_sonoff_ip
    else:
        sonoff_ip = snipeit_api.get_sonoff_ip_by_rte_ip(rte_ip)
    sonoff = SonoffDevice(sonoff_ip)
    return sonoff, sonoff_ip

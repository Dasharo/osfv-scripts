
from osfv.libs.sonoff_api import SonoffDevice

def init_sonoff(init_sonoff_ip, rte_ip, snipeit_api=None):
    sonoff_ip = ""
    sonoff = None
    if not snipeit_api:
        if not init_sonoff_ip:
            raise TypeError(
                f"Expected a value for 'sonoff_ip', but got None"
            )
        sonoff_ip = init_sonoff_ip
    else:
        sonoff_ip = snipeit_api.get_sonoff_ip_by_rte_ip(rte_ip)
        if not sonoff_ip:
            raise SonoffNotFound(
                exit(
                    f"Sonoff IP not found in SnipeIT for RTE: {rte_ip}")
            )
    sonoff = SonoffDevice(sonoff_ip)
    return sonoff, sonoff_ip

class SonoffNotFound(Exception):
    pass


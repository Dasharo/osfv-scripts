from osfv.libs.benchrack import BenchRack
from osfv.libs.models import Models
from osfv.libs.rte import RTE

# Bench drivers, keyed by the `bench` field of a DUT model config. A model that
# names no bench is on a plain RTE, which is how every bench in the lab was
# wired before benches with their own control hardware appeared.
BENCHES = {
    "rte": RTE,
    "benchrack": BenchRack,
}

DEFAULT_BENCH = "rte"


def new_bench(rte_ip, dut_model, sonoff):
    """
    Builds the bench driver the DUT model config asks for.

    Args:
        rte_ip (str): IP address of the RTE controlling the bench.
        dut_model (str): The DUT model name, naming its config file.
        sonoff (SonoffDevice): The Sonoff/Tasmota device switching mains.

    Returns:
        RTE: A driver for the bench, an RTE subclass.

    Raises:
        UnsupportedBench: If the config names a bench with no driver.
    """
    dut_data = Models().load_model_data(dut_model)[1]
    bench = dut_data.get("bench", DEFAULT_BENCH)
    driver = BENCHES.get(bench)
    if not driver:
        raise UnsupportedBench(
            f"The '{bench}' bench of model {dut_model} has no driver "
            f"(supported: {', '.join(sorted(BENCHES))})"
        )
    return driver(rte_ip, dut_model, sonoff)


class UnsupportedBench(Exception):
    pass

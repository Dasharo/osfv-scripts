from osfv.libs.models import Models
from osfv.libs.rte import RTE
from osfv.libs.rte_spi_mux import SPIMuxRTE


def new_rte(rte_ip, dut_model, sonoff):
    """
    Builds the driver for the RTE a DUT is wired to: a plain RTE, or one that
    drives the SPI mux extension when the model config declares `spi_mux`.

    Args:
        rte_ip (str): IP address of the RTE.
        dut_model (str): The DUT model name, naming its config file.
        sonoff (SonoffDevice): The Sonoff/Tasmota device switching mains.

    Returns:
        RTE: A driver for the RTE, either RTE itself or a subclass of it.
    """
    dut_data = Models().load_model_data(dut_model)[1]
    driver = SPIMuxRTE if dut_data.get("spi_mux") else RTE
    return driver(rte_ip, dut_model, sonoff)

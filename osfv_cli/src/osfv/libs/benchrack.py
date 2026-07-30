import os
import time

from osfv.libs.rte import (
    RTE,
    FlashImageSizeMismatch,
    PowerStateTimeout,
    SPIWrongVoltage,
    UnsupportedOperation,
)


class BenchRack(RTE):
    """
    A bench where two flashes, the host boot flash and the BMC flash, sit
    behind a 2:1 SPI mux driven by the RTE. Selected by `bench: benchrack` in
    the DUT model config.

    It differs from a plain RTE in three ways:

    - The mux occupies GPIO 13-16, so the power LED readback moves to GPIO 17
      and there is no CMOS-clear line.
    - A flash operation must route the bus to the addressed flash before
      energizing it, and leave both flashes isolated afterward.
    - Host power state is read back from the power LED, so powering the host
      off for a flash polls until it is actually off instead of assuming a
      button press worked.

    Mains/AC control is unchanged: the smart plug in front of the PSU is a
    Tasmota device, which is what `pwr_ctrl.sonoff` already drives.

    The GPIO assignment and the flash sequence mirror the `benchrack` driver in
    zarhus/benchctl (platform/benchrack.go); keep the two in step.
    """

    # GPIO 1-3 and 8-9 are open-collector ("low"/"high-z"), 13-19 push-pull
    # ("high"/"low"). 13-16 are the J10 expander pins the RTE reports as
    # ext0-ext3, 17 is the native J1 pin it reports as led1.
    GPIO_MUX_ENABLE = 13  # GPIO400, 2:1 mux enable
    GPIO_EN_HOST = 14  # E_GPA1, host flash load-switch enable
    GPIO_EN_BMC = 15  # E_GPA2, BMC flash load-switch enable
    GPIO_MUX_SELECT = 16  # 2:1 mux select
    GPIO_PWR_LED = 17  # DUT power LED readback

    # No CMOS-clear line is wired on this bench.
    GPIO_CMOS = None

    FLASH_TARGETS = ("host", "bmc")

    # The mux enable is active low: low routes the selected branch onto the bus,
    # high isolates both flashes. Select low routes to the host flash.
    MUX_ENABLE_ON = "low"
    MUX_ENABLE_OFF = "high"
    MUX_SELECT = {"host": "low", "bmc": "high"}

    # Load switch supplying each flash, on a board that has per-flash switches.
    ENABLE_GPIO = {"host": GPIO_EN_HOST, "bmc": GPIO_EN_BMC}

    # Stage a read on /data (persistent storage) rather than /tmp (tmpfs): the
    # RTE has little free RAM, and flashrom already holds roughly the flash size
    # in memory, so buffering a 64 MB image in RAM as well can exhaust it.
    FW_PATH_READ = "/data/read.rom"

    # Delay after energizing SPI Vcc, and again after the lines, to let the
    # rail settle before flashrom talks to the chip.
    SETTLE_SECS = 2

    POWER_POLL_INTERVAL_SECS = 1
    POWER_POLL_TIMEOUT_SECS = 60
    POWER_BUTTON_ON_SECS = 1
    POWER_BUTTON_OFF_SECS = 6

    def __init__(self, rte_ip, dut_model, sonoff):
        super().__init__(rte_ip, dut_model, sonoff)
        self.parked = False

    def park(self):
        """
        Drives the load switches and the SPI bus to a known-off state, leaving
        both flashes isolated from the RTE and connected to their board.

        Args:
            None.

        Returns:
            None.
        """
        self.gpio_set(self.GPIO_EN_BMC, "low")
        self.gpio_set(self.GPIO_EN_HOST, "low")
        self.gpio_set(self.GPIO_SPI_VCC, "high-z")
        self.gpio_set(self.GPIO_SPI_ON, "high-z")
        # Selecting the BMC branch freezes the BMC even with the mux disabled,
        # so the select never rests there.
        self.gpio_set(self.GPIO_MUX_SELECT, self.MUX_SELECT["host"])
        self.gpio_set(self.GPIO_MUX_ENABLE, self.MUX_ENABLE_OFF)
        self.parked = True

    def ensure_idle(self):
        """
        Parks the flash bus once per instance. A run killed part-way through a
        flash leaves the rail up and the mux routed, and powering the host on
        after that boots it while the RTE still drives its flash. Every
        operation parks first, so no run trusts the state another one left.

        Args:
            None.

        Returns:
            None.
        """
        if self.parked:
            return
        self.park()

    def flash_target_data(self, target=None):
        """
        Returns the flash chip configuration for a target.

        `flash_chip` describes the host flash, the default target. Any other
        flash is described by its own `flash_chip.targets` entry alone, so it
        does not inherit the host's chip model or size; only the bus voltage
        carries over, and the entry can override that too.

        Args:
            target (str, optional): The flash to describe. Defaults to the
            currently selected target.

        Returns:
            dict: The chip configuration ("model", "voltage", "size").
        """
        target = target or self.flash_target
        flash_chip = self.dut_data.get("flash_chip", {})
        if target == self.FLASH_TARGETS[0]:
            data = {
                key: flash_chip[key]
                for key in ("model", "voltage", "size")
                if key in flash_chip
            }
        else:
            data = {"voltage": flash_chip.get("voltage")}
        data.update(flash_chip.get("targets", {}).get(target, {}))
        return data

    def power_state(self):
        """
        Reads the host power state back from the power LED.

        Args:
            None.

        Returns:
            str: PSU_STATE_ON or PSU_STATE_OFF.
        """
        self.ensure_idle()
        state = self.gpio_get(self.GPIO_PWR_LED)
        polarity = self.dut_data.get("pwr_led", {}).get("polarity")
        if polarity == "active low":
            state = "low" if state == "high" else "high"
        return self.PSU_STATE_ON if state == "high" else self.PSU_STATE_OFF

    def set_power(self, state):
        """
        Presses the power button and polls the power LED until the host reaches
        the requested state. Does nothing if it is already there.

        Args:
            state (str): PSU_STATE_ON or PSU_STATE_OFF.

        Returns:
            None.

        Raises:
            PowerStateTimeout: If the host does not reach the state in time.
        """
        if self.power_state() == state:
            return
        if state == self.PSU_STATE_ON:
            self.power_on(self.POWER_BUTTON_ON_SECS)
        else:
            self.power_off(self.POWER_BUTTON_OFF_SECS)

        deadline = time.monotonic() + self.POWER_POLL_TIMEOUT_SECS
        while self.power_state() != state:
            if time.monotonic() >= deadline:
                raise PowerStateTimeout(
                    f"Timed out after {self.POWER_POLL_TIMEOUT_SECS}s waiting "
                    f"for the host to be {state}"
                )
            time.sleep(self.POWER_POLL_INTERVAL_SECS)

    def power_on(self, sleep=1):
        self.ensure_idle()
        super().power_on(sleep)

    def power_off(self, sleep=6):
        self.ensure_idle()
        super().power_off(sleep)

    def reset(self, sleep=1):
        self.ensure_idle()
        super().reset(sleep)

    def psu_on(self):
        self.ensure_idle()
        super().psu_on()

    def reset_cmos(self):
        raise UnsupportedOperation(
            "BenchRack has no CMOS clear line, clear the CMOS manually"
        )

    def spi_enable(self):
        """
        Routes the bus to the selected flash and energizes it: park, set the
        voltage, select and enable the mux branch, then bring up Vcc and the
        lines with a settle delay after each.

        Args:
            None.

        Returns:
            None.

        Raises:
            SPIWrongVoltage: If the target declares an unsupported voltage.
        """
        target = self.flash_target
        voltage = self.flash_target_data()["voltage"]
        if voltage == "1.8V":
            voltage_state = "high-z"
        elif voltage == "3.3V":
            voltage_state = "low"
        else:
            raise SPIWrongVoltage

        # Never trust the state an earlier run left behind.
        self.park()

        print(
            f"Routing the SPI bus to the {target} flash "
            f"(mux select {self.MUX_SELECT[target]}, {voltage})..."
        )
        self.gpio_set(self.GPIO_SPI_VOLTAGE, voltage_state)
        self.gpio_set(self.GPIO_MUX_SELECT, self.MUX_SELECT[target])
        # Enable the mux only once the branch is selected.
        self.gpio_set(self.GPIO_MUX_ENABLE, self.MUX_ENABLE_ON)
        self.parked = False
        # Bring up the SPI Vcc rail before closing the branch load switch, so
        # the switch never ties a de-energized rail to a flash that another
        # supply may still hold at voltage and back-drive the rail.
        self.gpio_set(self.GPIO_SPI_VCC, "low")
        if self.dut_data.get("flash_chip", {}).get("power_switches"):
            self.gpio_set(self.ENABLE_GPIO[target], "high")
        time.sleep(self.SETTLE_SECS)
        self.gpio_set(self.GPIO_SPI_ON, "low")
        time.sleep(self.SETTLE_SECS)

    def spi_disable(self):
        """
        Returns the bus and the load switches to idle, isolating both flashes.

        Args:
            None.

        Returns:
            None.
        """
        self.gpio_set(self.GPIO_SPI_ON, "high-z")
        # Open the load switches before dropping the SPI Vcc rail, isolating the
        # flash from the rail before it de-energizes so no external supply can
        # drive current back into it.
        self.gpio_set(self.GPIO_EN_BMC, "low")
        self.gpio_set(self.GPIO_EN_HOST, "low")
        self.gpio_set(self.GPIO_SPI_VCC, "high-z")
        self.gpio_set(self.GPIO_MUX_ENABLE, self.MUX_ENABLE_OFF)
        self.gpio_set(self.GPIO_MUX_SELECT, self.MUX_SELECT["host"])
        self.gpio_set(self.GPIO_SPI_VOLTAGE, "high-z")
        self.parked = True

    def pwr_ctrl_before_flash(self, programmer, power_state):
        """
        Moves the DUT into the power state external flashing needs, then
        energizes the selected flash. The RTE supplies the flash, so the host
        must be off first, confirmed through the power LED rather than assumed.

        Args:
            programmer (str): The programmer name from the model config.
            power_state (str): "S5" (soft off) or "G3" (mains removed).

        Returns:
            None.
        """
        self.ensure_idle()
        # Always start from the same state (mains applied), so the power button
        # has an effect and the LED readback is meaningful.
        self.psu_on()
        print("Powering the host off...")
        self.set_power(self.PSU_STATE_OFF)

        if power_state == "G3":
            print("Removing mains to put the host into G3...")
            self.psu_off()
            self.discharge_psu()
        elif power_state != "S5":
            exit(
                f"Power state: '{power_state}' is not supported. Please check "
                f"model config."
            )

        self.spi_enable()
        time.sleep(3)

    def pwr_ctrl_after_flash(self, programmer):
        """
        Isolates the flash bus again once flashing is done.

        Args:
            programmer (str): The programmer name from the model config.

        Returns:
            None.
        """
        self.spi_disable()
        time.sleep(2)

    def flash_create_args(self, extra_args=""):
        """
        Creates flashrom arguments for the selected flash, setting its chip
        model explicitly when the model config names one.

        Args:
            extra_args (str, optional): Additional flashrom arguments.

        Returns:
            str: The generated flashrom arguments.
        """
        args = ""
        model = self.flash_target_data().get("model")
        if model:
            args = " ".join(["-c", model])
        if extra_args:
            args = " ".join([args, extra_args])
        return args

    def flash_write(self, write_file, bios=False):
        """
        Writes firmware to the selected flash, refusing an image whose size
        does not match that flash. The two flashes differ in size, so this
        catches a host image aimed at the BMC and the other way round.

        Args:
            write_file (str): The path to the firmware file to write.
            bios (bool, optional): Whether to write the BIOS region only.

        Returns:
            The return code from the flashrom command execution.

        Raises:
            FlashImageSizeMismatch: If the image size does not match the flash.
        """
        expected = self.flash_target_data().get("size")
        if expected:
            size = os.path.getsize(write_file)
            if size != expected:
                raise FlashImageSizeMismatch(
                    f"{write_file} is {size} bytes, but the "
                    f"{self.flash_target} flash is {expected} bytes"
                )
        return super().flash_write(write_file, bios)

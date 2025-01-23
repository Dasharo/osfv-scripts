import os
import time
import subprocess
import sys


class LocalFlashError(Exception):
    pass


class LocalFlasher:
    """
    A local flasher:
     - toggles GPIO under /sys/class/gpio/gpioX/value
     - calls flashrom with local programmer
    """

    # same constants as in flash.sh
    GPIO_SPI_VOLTAGE = 517  # 0 => 1.8V, 1 => 3.3V
    GPIO_SPI_LINES   = 516  # 1 => lines on
    GPIO_SPI_VCC     = 518  # 1 => VCC on

    FLASHROM_PROGRAMMER = "linux_spi:dev=/dev/spidev1.0,spispeed=16000"

    def __init__(self, voltage="1.8V", flashrom_params=""):
        """
        :param voltage: "1.8V" or "3.3V"
        :param flashrom_params: extra flashrom args (optional)
        """
        self.voltage = voltage
        self.flashrom_params = flashrom_params

    def flashrom_cmd(self, extra_args):
        """
        Runs flashrom with the chosen programmer + any extra args
        """
        cmd = [
            "flashrom",
            "-p",
            f"{self.FLASHROM_PROGRAMMER}",
        ]
        if self.flashrom_params:
            cmd.extend(self.flashrom_params.split())
        cmd.extend(extra_args.split())

        print(f"[localflash] Running: {' '.join(cmd)}")
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            raise LocalFlashError(f"flashrom failed with code {e.returncode}")

    def set_gpio_value(self, gpio_no, value_str):
        """
        Writes '0' or '1' to /sys/class/gpio/gpioX/value
        """
        path = f"/sys/class/gpio/gpio{gpio_no}/value"
        if not os.path.exists(path):
            raise LocalFlashError(f"GPIO {gpio_no} not exported or not found at {path}")

        # Convert '0'/'1' from the given 'value_str' if needed
        if value_str == "0" or value_str == "1":
            val = value_str
        else:
            raise LocalFlashError(f"Bad gpio value: {value_str}")

        print(f"[localflash] echo {val} > {path}")
        with open(path, "w") as f:
            f.write(val)

    def spi_on(self):
        """
        Equivalent to flash.sh's `spiON()`:
          - sets voltage (gpio 517) to 0 => 1.8V or 1 => 3.3V
          - sets gpio 516 => 1 (SPI lines on)
          - sets gpio 518 => 1 (VCC on)
        """
        if self.voltage == "3.3V":
            print("[localflash] Setting SPI VCC to 3.3V")
            self.set_gpio_value(self.GPIO_SPI_VOLTAGE, "1")
        else:
            print("[localflash] Setting SPI VCC to 1.8V")
            self.set_gpio_value(self.GPIO_SPI_VOLTAGE, "0")

        time.sleep(1)
        print("[localflash] SPI lines on")
        self.set_gpio_value(self.GPIO_SPI_LINES, "1")

        time.sleep(1)
        print("[localflash] SPI Vcc on")
        self.set_gpio_value(self.GPIO_SPI_VCC, "1")

        time.sleep(2)

    def spi_off(self):
        """
        Equivalent to flash.sh's `spiOFF()`.
        """
        print("[localflash] SPI Vcc off")
        self.set_gpio_value(self.GPIO_SPI_VCC, "0")
        print("[localflash] SPI lines off")
        self.set_gpio_value(self.GPIO_SPI_LINES, "0")
        # set voltage to 0 => 1.8 again, or no
        self.set_gpio_value(self.GPIO_SPI_VOLTAGE, "0")

    def cmd_probe(self):
        # flashrom -p <programmer> ...
        self.spi_on()
        print("[localflash] Probing flash with flashrom")
        self.flashrom_cmd("")
        self.spi_off()

    def cmd_read(self, out_file):
        # flashrom -p <programmer> -r out_file
        self.spi_on()
        print(f"[localflash] Reading flash -> {out_file}")
        self.flashrom_cmd(f"-r {out_file} -V")
        self.spi_off()

    def cmd_write(self, in_file):
        # flashrom -p <programmer> -w in_file
        if not os.path.isfile(in_file):
            raise LocalFlashError(f"Input file {in_file} does not exist!")
        self.spi_on()
        print(f"[localflash] Writing {in_file} to flash...")
        self.flashrom_cmd(f"-w {in_file}")
        self.spi_off()

    def cmd_erase(self):
        # flashrom -p <programmer> -E
        self.spi_on()
        print("[localflash] Erasing entire flash...")
        self.flashrom_cmd("-E")
        self.spi_off()


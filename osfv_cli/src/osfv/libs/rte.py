import os
import sys
import time

import paramiko
import requests
import yaml
from importlib_resources import files
from osfv.libs.rtectrl_api import rtectrl
from voluptuous import Any, Optional, Required, Schema


class RTE(rtectrl):
    GPIO_SPI_ON = 1
    GPIO_SPI_VOLTAGE = 2
    GPIO_SPI_VCC = 3

    GPIO_RELAY = 0
    GPIO_RESET = 8
    GPIO_POWER = 9

    GPIO_CMOS = 12

    PSU_STATE_ON = "ON"
    PSU_STATE_OFF = "OFF"

    SSH_USER = "root"
    SSH_PWD = "meta-rte"
    FW_PATH_WRITE = "/data/write.rom"
    FW_PATH_READ = "/tmp/read.rom"

    PROGRAMMER_RTE = "linux_spi:dev=/dev/spidev1.0,spispeed=16000"
    PROGRAMMER_CH341A = "ch341a_spi"
    PROGRAMMER_DEDIPROG = "dediprog"
    FLASHROM_CMD = "flashrom -p {programmer} {args}"

    def __init__(self, rte_ip, dut_model, sonoff):
        self.rte_ip = rte_ip
        self.dut_model = dut_model
        self.dut_data = self.load_model_data()
        self.sonoff = sonoff
        if not self.sonoff_sanity_check():
            raise SonoffNotFound(
                exit(
                    f"Missing value for 'sonoff_ip' or Sonoff not found in SnipeIT"
                )
            )

    def load_model_data(self):
        """
        Loads and validates a YAML configuration file based on the device under test (DUT) model.

        The function loads a YAML file specific to the DUT model, validates its contents using a schema, and checks
        for the presence of required fields. If any issues are found, an exception is raised or the program exits.

        Args:
            None.

        Returns:
            dict: The loaded configuration data from the YAML file if it is valid.

        Raises:
            UnsupportedDUTModel: If the configuration file for the given DUT model is not found or supported.
            Exception: If the YAML file is invalid or if required fields are missing from the configuration.
        """
        file_path = os.path.join(
            files("osfv"), "models", f"{self.dut_model}.yml"
        )
        # Check if the file exists
        if not os.path.isfile(file_path):
            raise UnsupportedDUTModel(
                f"The {file_path} model is not yet supported"
            )

        # Load the YAML file
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        voltage_validator = Any("1.8V", "3.3V")
        programmer_name_validator = Any(
            "rte_1_1", "rte_1_0", "ch341a", "dediprog"
        )
        flashing_power_state_validator = Any("G3", "S5")

        schema = Schema(
            {
                Required("programmer"): {
                    Required("name"): programmer_name_validator,
                },
                Required("flash_chip"): {
                    Required("voltage"): voltage_validator,
                    Optional("model"): str,
                },
                Required("pwr_ctrl"): {
                    Required("sonoff"): bool,
                    Required("relay"): bool,
                    Required(
                        "flashing_power_state"
                    ): flashing_power_state_validator,
                },
                Optional("reset_cmos", default=False): bool,
                Optional("disable_wp", default=False): bool,
            }
        )

        try:
            schema(data)
        except Exception as e:
            exit(f"Model file is invalid: {e}")

        # Check if required fields are present
        required_fields = [
            "pwr_ctrl",
            "pwr_ctrl.sonoff",
            "pwr_ctrl.relay",
            "flash_chip",
            "flash_chip.voltage",
            "programmer",
            "programmer.name",
        ]
        for field in required_fields:
            current_field = data
            keys = field.split(".")
            for key in keys:
                if key in current_field:
                    current_field = current_field[key]
                else:
                    exit(
                        f"Required field '{field}' is missing in model config."
                    )

        # Return the loaded data
        return data

    def power_on(self, sleep=1):
        """
        Turns the power on by setting the power button pin to "low" for a
        specified duration.

        Args:
            sleep (int, optional): The duration (in seconds) to keep the
            power pin in the "low" state. Default is 1 second.

        Returns:
            None
        """
        self.gpio_set(self.GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def power_off(self, sleep=6):
        """
        Turns the power off by setting the power button pin to "low" for a
        specified duration.

        Args:
            sleep (int, optional): The duration (in seconds) to keep the power
            pin in the "low" state. Default is 6 seconds.

        Returns:
            None
        """
        self.gpio_set(self.GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def reset(self, sleep=1):
        """
        Resets the system by setting the reset button pin to "low" for a
        specified duration.

        Args:
            sleep (int, optional): The duration (in seconds) to keep the reset
            pin in the "low" state. Default is 1 second.

        Returns:
            None
        """
        self.gpio_set(self.GPIO_RESET, "low", sleep)
        time.sleep(sleep)

    def relay_get(self):
        """
        Retrieves the current state of the relay.

        Returns:
            str: The state of the relay, either "on" if the GPIO relay pin is
                 "high", or "off" if the GPIO relay pin is "low".
        """
        gpio_state = self.gpio_get(self.GPIO_RELAY)
        relay_state = None
        if gpio_state == "high":
            relay_state = self.PSU_STATE_ON
        if gpio_state == "low":
            relay_state = self.PSU_STATE_OFF
        return relay_state

    def relay_set(self, relay_state):
        """
        Sets the state of the relay by configuring the GPIO relay pin accordingly.

        Args:
            relay_state (str): Desired state of the relay, either "on" (sets GPIO pin to "high")
                               or "off" (sets GPIO pin to "low").

        Returns:
            None
        """
        gpio_state = None
        if relay_state == self.PSU_STATE_ON:
            gpio_state = "high"
        if relay_state == self.PSU_STATE_OFF:
            gpio_state = "low"
        self.gpio_set(self.GPIO_RELAY, gpio_state)

    def reset_cmos(self):
        """
        Resets the CMOS by setting the GPIO CMOS pin to "low" for 10 seconds, then returning it to a "high-z" state.

        Args:
            None.

        Returns:
            None.
        """
        self.gpio_set(self.GPIO_CMOS, "low")
        time.sleep(10)
        self.gpio_set(self.GPIO_CMOS, "high-z")

    def spi_enable(self):
        """
        Enable the SPI interface by configuring GPIO pins based on the voltage level required by the flash chip.

        Args:
            None.

        Returns:
            None.
        """
        voltage = self.dut_data["flash_chip"]["voltage"]

        if voltage == "1.8V":
            state = "high-z"
        elif voltage == "3.3V":
            state = "low"
        else:
            raise SPIWrongVoltage

        self.gpio_set(self.GPIO_SPI_VOLTAGE, state)
        time.sleep(2)
        self.gpio_set(self.GPIO_SPI_VCC, "low")
        time.sleep(2)
        self.gpio_set(self.GPIO_SPI_ON, "low")
        time.sleep(10)

    def spi_disable(self):
        """
        Disable the SPI interface by setting the GPIO pins to a "high-z" state.

        Args:
            None.

        Returns:
            None.
        """
        self.gpio_set(self.GPIO_SPI_VCC, "high-z")
        self.gpio_set(self.GPIO_SPI_ON, "high-z")

    def psu_on(self):
        """
        Connect main power supply to the DUT by setting either relay or Sonoff to ON state.

        Args:
            None.

        Returns:
            None.
        """
        if self.dut_data["pwr_ctrl"]["sonoff"] is True:
            self.sonoff.turn_on()
            state = self.sonoff.get_state()
            if state != self.PSU_STATE_ON:
                raise Exception("Failed to power control ON")
        elif self.dut_data["pwr_ctrl"]["relay"] is True:
            self.relay_set(self.PSU_STATE_ON)
            state = self.relay_get()
            if state != self.PSU_STATE_ON:
                raise Exception("Failed to power control ON")
        time.sleep(5)

    def psu_off(self):
        """
        Disconnect main power supply from the DUT by setting either relay or Sonoff to OFF state.

        Args:
            None.

        Returns:
            None.
        """
        # TODO: rework using abstract interfaces for power control?
        if self.dut_data["pwr_ctrl"]["sonoff"] is True:
            self.sonoff.turn_off()
            state = self.sonoff.get_state()
            if state != self.PSU_STATE_OFF:
                raise Exception("Failed to power control OFF")
        elif self.dut_data["pwr_ctrl"]["relay"] is True:
            self.relay_set(self.PSU_STATE_OFF)
            state = self.relay_get()
            if state != self.PSU_STATE_OFF:
                raise Exception("Failed to power control OFF")
        time.sleep(2)

    def psu_get(self):
        """
        Get the current state of the Power Supply Unit (PSU).

        Args:
            None.

        Returns:
            str or None: The state of the PSU, which could be "ON", "OFF", or None if no valid PSU state is found.
        """
        state = None
        if self.dut_data["pwr_ctrl"]["sonoff"] is True:
            state = self.sonoff.get_state()
        elif self.dut_data["pwr_ctrl"]["relay"] is True:
            state = self.relay_get()
        return state

    def discharge_psu(self):
        """
        Push power button 5 times in the loop to make sure the charge from PSU is dissipated.

        Args:
            None.

        Returns:
            None.
        """
        for _ in range(5):
            self.power_off(3)

    def pwr_ctrl_before_flash(self, programmer, power_state):
        """
        Moves the Device Under Test (DUT) into the required power state for external flashing operations,
        based on the model configuration file. The function handles power sequencing and ensures the DUT is
        in the correct state (S5 or G3) before flashing.

        Args:
            programmer (str): The programmer type, used to determine if SPI lines need to be enabled.
            power_state (str): The desired power state for flashing, either "S5" (off) or "G3" (powered off).

        Returns:
            None.
        """
        # Always start from the same state (PSU active)
        self.psu_on()
        time.sleep(5)
        # Put the device into S5 state
        self.power_off(6)
        time.sleep(10)

        # Some platforms need to enable SPI lines at this point
        # when PSU is active (e.g. VP6650). Otherwise the chip is not detected.
        # So we must turn the PSU ON first in the middle of power cycle,
        # even if we perform flashing with the PSU OFF (G3).
        if programmer == "rte_1_1":
            self.spi_enable()
            time.sleep(3)

        if power_state == "S5":
            # Nothing to do, we just entered the S5 state
            pass
        elif power_state == "G3":
            # Turn off the PSU/AC brick to put device into G3
            self.psu_off()
            self.discharge_psu()
        else:
            exit(
                f"Power state: '{power_state}' is not supported. Please check model config."
            )

    def pwr_ctrl_after_flash(self, programmer):
        """
        Additional power actions to take after flashing.

        Args:
            programmer (str): The programmer type, used to determine if SPI lines need to be enabled.

        Returns:
            None.
        """
        if programmer == "rte_1_1":
            self.spi_disable()
            time.sleep(2)

    def flash_cmd(self, args, read_file=None, write_file=None):
        """
        Send the firmware file to RTE and execute flashrom command over SSH to flash the DUT.

        Args:
        args (str): Arguments to be passed to the flashrom command.
        read_file (str, optional): Path to save the read firmware file after flashing. Defaults to None.
        write_file (str, optional): Path to the firmware file to be written to the DUT. Defaults to None.

    Returns:
        None.
        """
        try:
            self.pwr_ctrl_before_flash(
                self.dut_data["programmer"]["name"],
                self.dut_data["pwr_ctrl"]["flashing_power_state"],
            )
        except requests.exceptions.ConnectionError as e:
            print(f"Failed to change power state while flashing: {e}")
            raise SystemExit

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to the SSH server
            ssh.connect(
                self.rte_ip,
                username=self.SSH_USER,
                password=self.SSH_PWD,
                look_for_keys=False,
            )

            if write_file:
                scp = ssh.open_sftp()
                scp.put(write_file, self.FW_PATH_WRITE)
                scp.close()

            # Execute the flashrom command
            if self.dut_data["programmer"]["name"] == "ch341a":
                flashrom_programmer = self.PROGRAMMER_CH341A
            elif self.dut_data["programmer"]["name"] == "dediprog":
                flashrom_programmer = self.PROGRAMMER_DEDIPROG
            else:
                flashrom_programmer = self.PROGRAMMER_RTE

            command = self.FLASHROM_CMD.format(
                programmer=flashrom_programmer, args=args
            )
            print(f"Executing command: {command}")

            channel = ssh.get_transport().open_session()
            channel.exec_command(command)

            # Print the command output in real-time
            while True:
                if channel.exit_status_ready():
                    break
                if channel.recv_ready():
                    stdout = channel.recv(1024).decode()
                    if stdout:
                        print(stdout, end="")
                if channel.recv_stderr_ready():
                    stderr = channel.recv_stderr(1024).decode()
                    if stderr:
                        print(stderr, end="", file=sys.stderr)

            # Ensure all remaining output is captured after the loop exits
            while channel.recv_ready():
                stdout = channel.recv(1024).decode()
                if stdout:
                    print(stdout, end="")

            while channel.recv_stderr_ready():
                stderr = channel.recv_stderr(1024).decode()
                if stderr:
                    print(stderr, end="", file=sys.stderr)

            # Get the return code from flashrom process
            flashrom_rc = channel.recv_exit_status()

            if read_file:
                scp = ssh.open_sftp()
                scp.get(self.FW_PATH_READ, read_file)
                scp.close()

        finally:
            self.pwr_ctrl_after_flash(self.dut_data["programmer"]["name"])

            # Close the SSH connection
            ssh.close()

        return flashrom_rc

    def flash_create_args(self, extra_args=""):
        """
        Creates flashrom arguments based on the DUT model configuration, including any extra arguments provided.
        It explicitly sets the flash chip model if defined in the configuration and appends any additional arguments.

        Args:
            extra_args (str, optional): Additional arguments to be added to the flashrom command. Defaults to an empty string.

        Returns:
            str: The generated flashrom arguments as a string.
        """
        args = ""

        # Set chip explicitly, if defined in model configuration
        if "flash_chip" in self.dut_data:
            if "model" in self.dut_data["flash_chip"]:
                args = " ".join(["-c", self.dut_data["flash_chip"]["model"]])

        if extra_args:
            args = " ".join([args, extra_args])

        return args

    def flash_probe(self):
        """
        Execute flashrom with no commands to simply probe the flash chip.

        Args:
            None.

        Returns:
            None.
        """
        args = self.flash_create_args()
        return self.flash_cmd(args)

    def flash_read(self, read_file):
        """
        Executes the flashrom command to read the firmware from the DUT and saves it to the specified file.

        Args:
            read_file (str): The file path where the firmware should be saved.

        Returns:
            int: The return code from the flashrom command execution.
        """
        args = self.flash_create_args(f"-r {self.FW_PATH_READ}")
        return self.flash_cmd(args, read_file=read_file)

    def flash_erase(self):
        """
        Executes the flashrom command to erase the flash chip on the DUT.

        Args:
            None.

        Returns:
            int: The return code from the flashrom command execution.
        """
        args = self.flash_create_args(f"-E")
        return self.flash_cmd(args)

    def flash_write(self, write_file, bios=False):
        """
        Executes the flashrom command to write firmware to the DUT.

        Args:
            write_file (str): The path to the firmware file to write.
            bios (bool, optional): If True, writes the BIOS image using the specific option. Defaults to False.

        Returns:
            int: The return code from the flashrom command execution.
        """
        if "disable_wp" in self.dut_data:
            args = self.flash_create_args("--wp-disable --wp-range=0x0,0x0")
            self.flash_cmd(args)
        if bios:
            args = self.flash_create_args(
                f"-i bios --ifd -w {self.FW_PATH_WRITE}"
            )
        else:
            args = self.flash_create_args(f"-w {self.FW_PATH_WRITE}")
        rc = self.flash_cmd(args, write_file=write_file)
        time.sleep(2)
        if "reset_cmos" in self.dut_data:
            if self.dut_data["reset_cmos"] == True:
                self.reset_cmos()
        return rc

    def sonoff_sanity_check(self):
        """
        Verifies that if the DUT is powered by Sonoff, the Sonoff IP is not None.

        Args:
            None.

        Returns:
            bool: True if the Sonoff is not used or the Sonoff IP is available; False otherwise.
        """
        return not self.dut_data["pwr_ctrl"]["sonoff"] or self.sonoff.sonoff_ip


class IncompleteModelData(Exception):
    pass


class UnsupportedDUTModel(Exception):
    pass


class SPIWrongVoltage(Exception):
    pass


class SonoffNotFound(Exception):
    pass

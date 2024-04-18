import os
import time

import paramiko
import yaml
from importlib_resources import files
from voluptuous import Any, Optional, Required, Schema

from osfv.libs.rtectrl_api import rtectrl
from osfv.libs.sonoff_api import SonoffDevice


class RTE(rtectrl):
    GPIO_SPI_ON = 1
    GPIO_SPI_VOLTAGE = 2
    GPIO_SPI_VCC = 3

    GPIO_RELAY = 0
    GPIO_RESET = 8
    GPIO_POWER = 9

    GPIO_CMOS = 12

    SSH_USER = "root"
    SSH_PWD = "meta-rte"
    FW_PATH_WRITE = "/tmp/write.rom"
    FW_PATH_READ = "/tmp/read.rom"

    PROGRAMMER_RTE = "linux_spi:dev=/dev/spidev1.0,spispeed=16000"
    PROGRAMMER_CH341A = "ch341a_spi"
    FLASHROM_CMD = "flashrom -p {programmer} {args}"

    def __init__(self, rte_ip, dut_model, snipeit_api=None, sonoff_ip= None):
        self.rte_ip = rte_ip
        self.dut_model = dut_model
        self.dut_data = self.load_model_data()
        self.snipeit_api = snipeit_api
        self.sonoff, self.sonoff_ip = self.init_sonoff(sonoff_ip)

    def load_model_data(self):
        file_path = os.path.join(files("osfv"), "models", f"{self.dut_model}.yml")

        # Check if the file exists
        if not os.path.isfile(file_path):
            raise UnsupportedDUTModel(
                f"The {self.dut_model} model is not yet supported"
            )

        # Load the YAML file
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        voltage_validator = Any("1.8V", "3.3V")
        programmer_name_validator = Any("rte_1_1", "rte_1_0", "ch341a")

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
                    Required("init_on"): bool,
                },
                Optional("reset_cmos", default=False): bool,
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
                    exit(f"Required field '{field}' is missing in model config.")

        # Return the loaded data
        return data

    def init_sonoff(self, init_sonoff_ip):
        sonoff_ip = ""
        sonoff = None

        if self.dut_data["pwr_ctrl"]["sonoff"] is True:
            if not self.snipeit_api:
                if not init_sonoff_ip:
                    raise TypeError(f"Expected a value for 'sonoff_ip', but got {init_sonoff_ip}")
                return SonoffDevice(init_sonoff_ip), init_sonoff_ip
            sonoff_ip = self.snipeit_api.get_sonoff_ip_by_rte_ip(self.rte_ip)
            if not sonoff_ip:
                raise SonoffNotFound(
                    exit(f"Sonoff IP not found in SnipeIT for RTE: {self.rte_ip}")
                )
            sonoff = SonoffDevice(sonoff_ip)

        return sonoff, sonoff_ip

    def power_on(self, sleep=1):
        self.gpio_set(self.GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def power_off(self, sleep=6):
        self.gpio_set(self.GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def reset(self, sleep=1):
        self.gpio_set(self.GPIO_RESET, "low", sleep)
        time.sleep(sleep)

    def relay_get(self):
        gpio_state = self.gpio_get(self.GPIO_RELAY)
        relay_state = None
        if gpio_state == 'high':
            relay_state = 'on'
        if gpio_state == 'low':
            relay_state = 'off'
        return relay_state

    def relay_set(self, relay_state):
        gpio_state = None
        if relay_state == 'on':
            gpio_state = 'high'
        if relay_state == 'off':
            gpio_state = 'low'
        self.gpio_set(self.GPIO_RELAY, gpio_state)

    def reset_cmos(self):
        self.gpio_set(self.GPIO_CMOS, "low")
        time.sleep(10)
        self.gpio_set(self.GPIO_CMOS, "high-z")

    def spi_enable(self):
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
        self.gpio_set(self.GPIO_SPI_VCC, "high-z")
        self.gpio_set(self.GPIO_SPI_ON, "high-z")

    def pwr_ctrl_on(self):
        if self.dut_data["pwr_ctrl"]["sonoff"] is True:
            self.sonoff.turn_on()
            state = self.sonoff.get_state()
            if state != "ON":
                raise Exception("Failed to power control ON")
        elif self.dut_data["pwr_ctrl"]["relay"] is True:
            self.relay_set("on")
            state = self.relay_get()
            if state != "on":
                raise Exception("Failed to power control ON")
        time.sleep(5)

    def pwr_ctrl_off(self):
        if self.dut_data["pwr_ctrl"]["sonoff"] is True:
            self.sonoff.turn_off()
            state = self.sonoff.get_state()
            if state != "OFF":
                raise Exception("Failed to power control OFF")
        elif self.dut_data["pwr_ctrl"]["relay"] is True:
            self.relay_set("off")
            state = self.relay_get()
            if state != "off":
                raise Exception("Failed to power control OFF")
        time.sleep(2)

    def discharge_psu(self):
        """
        Push power button 5 times in the loop to make sure the charge from PSU is dissipated
        """
        for _ in range(5):
            self.power_off(3)

    def pwr_ctrl_before_flash(self, programmer):
        # 1. sonoff/relay ON
        # 2. sleep 5
        # Some flash scripts started with power platform ON, but some others
        # not (like FW4C).
        if self.dut_data["pwr_ctrl"]["init_on"] is True:
            self.pwr_ctrl_on()
            time.sleep(5)
            self.power_off(6)
            time.sleep(10)
        else:
            # 3. RTE POFF
            # 4. sleep 3
            self.pwr_ctrl_off()
            self.discharge_psu()

        if programmer == "rte_1_1":
            # 5. SPI ON
            # 6. sleep 2
            self.spi_enable()
            time.sleep(3)

        if self.dut_data["pwr_ctrl"]["init_on"] is True:
            # 7. sonoff/relay OFF
            # 8. sleep 2
            self.pwr_ctrl_off()
            self.discharge_psu()

    def pwr_ctrl_after_flash(self, programmer):
        if programmer == "rte_1_1":
            # 10. SPI OFF
            # 11. sleep 2
            self.spi_disable()
            time.sleep(2)

    def flash_cmd(self, args, read_file=None, write_file=None):
        self.pwr_ctrl_before_flash(self.dut_data["programmer"]["name"])

        # 9. flashrom

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to the SSH server
            ssh.connect(self.rte_ip, username=self.SSH_USER, password=self.SSH_PWD)

            if write_file:
                scp = ssh.open_sftp()
                scp.put(write_file, self.FW_PATH_WRITE)
                scp.close()

            # Execute the flashrom command
            if self.dut_data["programmer"]["name"] == "ch341a":
                flashrom_programmer = self.PROGRAMMER_CH341A
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
                print(channel.recv(1024).decode())

            if read_file:
                scp = ssh.open_sftp()
                scp.get(self.FW_PATH_READ, read_file)
                scp.close()

        finally:
            self.pwr_ctrl_after_flash(self.dut_data["programmer"]["name"])

            # Close the SSH connection
            ssh.close()

    def flash_create_args(self, extra_args=""):
        args = ""

        # Set chip explicitly, if defined in model configuration
        if "flash_chip" in self.dut_data:
            if "model" in self.dut_data["flash_chip"]:
                args = " ".join(["-c", self.dut_data["flash_chip"]["model"]])

        if extra_args:
            args = " ".join([args, extra_args])

        return args

    def flash_probe(self):
        args = self.flash_create_args()
        self.flash_cmd(args)

    def flash_read(self, read_file):
        args = self.flash_create_args(f"-r {self.FW_PATH_READ}")
        self.flash_cmd(args, read_file=read_file)

    def flash_erase(self):
        args = self.flash_create_args(f"-E")
        self.flash_cmd(args)

    def flash_write(self, write_file):
        args = self.flash_create_args(f"-w {self.FW_PATH_WRITE}")
        self.flash_cmd(args, write_file=write_file)
        time.sleep(2)
        if "reset_cmos" in self.dut_data:
            if self.dut_data["reset_cmos"] == True:
                self.reset_cmos()


class IncompleteModelData(Exception):
    pass


class UnsupportedDUTModel(Exception):
    pass


class SPIWrongVoltage(Exception):
    pass


class SonoffNotFound(Exception):
    pass

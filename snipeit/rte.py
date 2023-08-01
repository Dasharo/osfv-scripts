from sonoff_api import SonoffDevice
from rtectrl_api import rtectrl 
import snipeit_api
import time
import paramiko
import yaml
import os

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

    PROGRAMMER = 'linux_spi:dev=/dev/spidev1.0,spispeed=16000'
    FLASHROM_CMD = 'flashrom -p {programmer} {args}'

    def __init__(self, rte_ip, dut_model):
        self.rte_ip = rte_ip
        self.dut_model = dut_model 
        self.dut_data = self.load_model_data()
        self.sonoff, self.sonoff_ip = self.init_sonoff()

    def load_model_data(self):
        # Specify the file path
        file_path = f"models/{self.dut_model}.yml"

        # Check if the file exists
        if not os.path.isfile(file_path):
            raise UnsupportedDUTModel("The given model is not yet supported")

        # Load the YAML file
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        # Return the loaded data
        return data

    def init_sonoff(self):
        sonoff_ip = ''
        sonoff = None

        if self.dut_data["pwr_ctrl"]["sonoff"] is True:
            sonoff_ip = snipeit_api.get_sonoff_ip_by_rte_ip(self.rte_ip)
            if not sonoff_ip:
                raise SonoffNotFound(f"Sonoff IP not found in SnipeIT for RTE: {self.rte_ip}")
            sonoff = SonoffDevice(sonoff_ip)

        return sonoff, sonoff_ip

    def power_on(self, sleep=1):
        self.gpio_set(self.GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def power_off(self, sleep=5):
        self.gpio_set(self.GPIO_POWER, "low", sleep)
        time.sleep(sleep)

    def reset(self, sleep=1):
        self.gpio_set(self.GPIO_RESET, "low", sleep)
        time.sleep(sleep)

    def relay_get(self):
        return self.gpio_get(self.GPIO_RELAY) 

    def relay_set(self, state):
        self.gpio_set(self.GPIO_RELAY, state)

    def reset_cmos(self):
        self.gpio_set(self.GPIO_CMOS, "low")
        time.sleep(10)
        self.gpio_set(self.GPIO_CMOS, "high-z")

    def spi_enable(self):
        if "flash_chip" in self.dut_data:
            if "voltage" in self.dut_data["flash_chip"]:
                voltage = self.dut_data["flash_chip"]["voltage"]
            else:
                raise IncompleteModelData("Flash chip voltage is missing in model data")

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
        time.sleep(2)

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
            self.relay_set("high")
            state = self.relay_get()
            if state != "high":
                raise Exception("Failed to power control ON")
        time.sleep(5)

    def pwr_ctrl_off(self):
        if self.dut_data["pwr_ctrl"]["sonoff"] is True:
            self.sonoff.turn_off()
            state = self.sonoff.get_state()
            if state != "OFF":
                raise Exception("Failed to power control OFF")
        elif self.dut_data["pwr_ctrl"]["relay"] is True:
            self.relay_set("low")
            state = self.relay_get()
            if state != "low":
                raise Exception("Failed to power control OFF")
        time.sleep(2)

    def flash_cmd(self, args, read_file=None, write_file=None):
        # 1. sonoff/relay ON
        # 2. sleep 5
        self.pwr_ctrl_on()

        # 3. RTE POFF
        # 4. sleep 3
        self.power_off(3)

        # 5. SPI ON
        # 6. sleep 2
        self.spi_enable()
        time.sleep(2)

        # 7. sonoff/relay OFF
        # 8. sleep 2
        self.pwr_ctrl_off()

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
            command = self.FLASHROM_CMD.format(programmer=self.PROGRAMMER, args=args)
            print(f'Executing command: {command}')
    
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
            # Close the SSH connection
            ssh.close()

            # 10. SPI OFF
            # 11. sleep 2
            self.spi_disable()
            time.sleep(2)

    def flash_create_args(self, extra_args=""):
        args = ""

        # Set chip explicitely, if defined in model configuration
        if "flash_chip" in self.dut_data:
            if "model" in self.dut_data["flash_chip"]:
                args = " ".join(['-c', self.dut_data["flash_chip"]["model"]])

        if extra_args:
            args = " ".join([args, extra_args])

        return args

    def flash_probe(self):
        args = self.flash_create_args()
        self.flash_cmd(args)

    def flash_read(self, read_file):
        args = self.flash_create_args(f'-r {self.FW_PATH_READ}') 
        self.flash_cmd(args, read_file=read_file)

    def flash_erase(self):
        args = self.flash_create_args(f'-E') 
        self.flash_cmd(args)

    def flash_write(self, write_file):
        args = self.flash_create_args(f'-w {self.FW_PATH_WRITE}') 
        self.flash_cmd(args, write_file=write_file)
        time.sleep(2)
        if 'reset_cmos' in self.dut_data:
            if self.dut_data['reset_cmos'] == True:
                self.reset_cmos()

class IncompleteModelData(Exception):
    pass

class UnsupportedDUTModel(Exception):
    pass

class SPIWrongVoltage(Exception):
    pass

class SonoffNotFound(Exception):
    pass

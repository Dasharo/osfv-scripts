from rtectrl_api import rtectrl 
import time
import paramiko

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

    def spi_enable(self, voltage):
        if voltage == "1.8V":
            state = "high-z"
        elif voltage == "3.3V":
            state = "low"
        else:
            raise SPIWrongVoltage

        self.gpio_set(self.GPIO_SPI_VOLTAGE, "high-z")
        self.gpio_set(self.GPIO_SPI_VCC, "low")
        self.gpio_set(self.GPIO_SPI_ON, "low")

    def spi_disable(self):
        self.gpio_set(self.GPIO_SPI_VCC, "high-z")
        self.gpio_set(self.GPIO_SPI_ON, "high-z")

    def flash_cmd(self, args, read_file=None, write_file=None):
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

    def flash_probe(self, args):
        self.flash_cmd(args)

    def flash_read(self, args, read_file):
        args = " ".join([args , '-r', self.FW_PATH_READ]) 
        self.flash_cmd(args, read_file=read_file)

    def flash_erase(self, args):
        args = " ".join([args , '-E']) 
        self.flash_cmd(args)

    def flash_write(self, args, write_file):
        args = " ".join([args , '-w', self.FW_PATH_WRITE]) 
        self.flash_cmd(args, write_file=write_file)

class SPIWrongVoltage(Exception):
    pass

# OSFV CLI

This script allows you to interact with devices setup in the Dasharo OSFV lab.
You can use this script to retrieve information about assets, list used and
unused assets, check out and check in assets, control power of the devices, flash
firmware, and more.

This script is specific to the OSFV environment and Snipe-IT configuration, and
as such, may not fit for other needs.

## Installation

1. Clone the repository to your local machine:

   ```shell
   git clone https://github.com/dasharo/osfv-scripts.git
   ```

1. Create virtual environment and activate it:

   ```shell
   virtualenv venv
   ```

   ```shell
   source venv/bin/activate
   ```

1. Navigate to the cloned repository:

   ```shell
   cd osfv-scripts/osfv_cli
   ```

1. Install poetry:

   ```shell
   pip install poetry
   ```

1. Build and install utility:

   ```shell
   make install
   ```

## Usage

> If you do not wish to use Snipe-IT, you can manually provide your device
> model name to the script via the `--model` parameter.

### Customize the configuration

> The `~/.osfv/snipeit.yml` should be created automatically upon installing
> the utility as shown above.

- Open `~/.osfv/snipeit.yml` and provide your Snipe-IT API URL, API token, and
  user ID
    + `api_url` - typically should be left unchanged, please make sure you have
    correct DNS configuration or entry in `/etc/hosts`,
    + `api_token` - login to Snipe-IT, click on user icon, choose `Manage API
Keys`, click `Create New Token`, use name `osfv-scripts`, use generated API
    token in config file
    + `user_id` is your Snipe-IT user id, which can be found by going to
    <http://snipeit/users> and showing column ID

To use the script, you can run it with different commands and options. The full
list of commands and description of arguments is in the help message. Here are
just some examples.

### snipeit command

- List all used assets:

  ```shell
  osfv_cli snipeit list_used
  ```

- List all unused assets:

  ```shell
  osfv_cli snipeit list_unused
  ```

- List all assets:

  ```shell
  osfv_cli snipeit list_all
  ```

- Check out an asset (by asset ID):

  ```shell
  osfv_cli snipeit check_out --asset_id 123
  ```

- Check in an asset (by asset ID):

  ```shell
  osfv_cli snipeit check_in --asset_id 123
  ```

- Check out an asset (by RTE IP):

  ```bash
  osfv_cli snipeit check_out --rte_ip <rte_ip_address>
  ```

- Check out an asset (by RTE IP):

  ```bash
  osfv_cli snipeit check_out --rte_ip <rte_ip_address>
  ```

- Check in all your assets:

  ```bash
  osfv_cli snipeit check_in_my
  ```

  > Replace `<rte_ip_address>` with the actual RTE IP address of the asset you
  > want to check out. The script will identify the asset based on the RTE IP and
  > perform the check-out process.
  > Please note that the RTE IP should match the value stored in the asset's
  > custom field named "RTE IP".

- For more command options, you can use the `--help` flag.

### sonoff command

- Get Sonoff state:

  ```bash
  osfv_cli sonoff --sonoff_ip <sonoff_ip_address> get
  ```

- Set Sonoff state to ON:

  ```bash
  osfv_cli sonoff --sonoff_ip <sonoff_ip_address> on
  ```

- Set Sonoff state to OFF:

  ```bash
  osfv_cli sonoff --sonoff_ip <sonoff_ip_address> off
  ```

- Toggle Sonoff state:

  ```bash
  osfv_cli sonoff --sonoff_ip <sonoff_ip_address> tgl
  ```

  > Replace `<sonoff_ip_address>` with the IP address of correct Sonoff. You
  > may also use `--rte_ip` instead, and Sonoff IP will be retrieved from
  > Snipe-IT if found.

### rte command

- Toggle relay state:

  ```bash
  osfv_cli rte --rte_ip <rte_ip_address> rel tgl
  ```

- Turn on the power supply of the platform:

  ```bash
  osfv_cli rte --rte_ip <rte_ip_address> pwr psu on
  ```

- Power on the platform (push power button):

  ```bash
  osfv_cli rte --rte_ip <rte_ip_address> pwr on
  ```

- List state of controllable GPIOs:

  ```bash
  osfv_cli rte --rte_ip <rte_ip_address> gpio list
  ```

- Enable SPI lines:

  ```bash
  osfv_cli rte --rte_ip <rte_ip_address> spi on
  ```

- Connect to DUT serial port connected  to RTE via telnet:

  ```bash
  osfv_cli rte --rte_ip <rte_ip_address> serial
  ```

- Flash DUT with given firmware file:

  > flash commands already take care of getting the platform in the correct
  > power state, and setting correct flashing parameters for certain device model,
  > as defined in the config files in `osfv_cli/models`

  ```bash
  osfv_cli rte --rte_ip <rte_ip_address> flash write --rom <path_to_fw_file>
  ```

  > Replace `<rte_ip_address>` with the actual RTE IP address connected with
  > the DUT.

### list_models command

List supported DUT models, available models/*.yml files are verified for existence
of all mandatory parameters, as described in next section.

  ```bash
  osfv_cli list_models
  ```

## Adding new platform configs

Platform configs hold information on power management, flash chip parameters,
and whether CMOS needs to be reset after flashing. All currently available
platform configs are located in the models directory. If you wish to expand
the list, you can place your `MODEL.yml` with corresponding settings in the
directory, following other configs' syntax. Available parameters are as
follows:

- `flash_chip`:

    + `model` - optional, needs to be set if flashrom detects more than one
    possible flash chip model - in other words, the `-c` parameter you use in
    flashrom.
    + `voltage` - required; chip supply voltage - most often "3.3V" or "1.8V";
    should be discovered in appropriate datasheet.

- `programmer`:

    + `name`- required; name of the programmer connected to the platform; supported
    values: `rte_1_0`, `rte_1_1`, `ch341a`

- `pwr_ctrl`:

    + `sonoff` - required; true or false, whether you use sonoff power control.
    + `relay` - required; true or false, whether you use onboard RTE relay
    power control.
    + `flashing_power_state` - required; defines a power state the platform
    needs to be in for SPI flashing; supported values: `"S5"`, `"G3"`

- `reset_cmos`: - optional; true or false (false by default), whether CMOS reset
  is required after flashing.

- `disable_wp`: - optional; true or false (false by default), whether flash WP
   is required before flashing.

## Known issues

### Problems with password-protected SSH keys

If your default SSH key is password-protected, make sure that 'SSH_AUTH_SOCK'
variable is either empty or deleted. Otherwise, you will be asked for key's
passphrase; despite correct answer, SSH code may throw time-out exception or
crash. To avoid this issue, you may either make variable empty:

  ```bash
SSH_AUTH_SOCK=""
  ```

or delete the variable:

  ```bash
unset SSH_AUTH_SOCK
  ```

## Development

You can test local changes by running `poetry shell` first. Then, all
`osfv_cli` calls will use the local files in repository, not installed package.

## Tests

OSFV CLI tests can be found in the `test` directory.
The tests are written in [Robot Framework](https://robotframework.org/),

### Dependencies

Enter development shell with test dependencies:

```shell
poetry install --with test
poetry shell
```

### Required configs

To test some functionalities related to SnipeIT, it is required to
use a configuration of a second SnipeIT user. The configuration
should be located at `~/.osfv-robot/snipeit.yaml`.
The API key and User ID must be valid, and different
from the one at `~/.osfv/snipeit.yaml`.
For details on SnipeIT configuration see [Customize the configuration](#customize-the-configuration).

### Running tests

When all the prerequisites are met, the test can be run:

```shell
robot test
```

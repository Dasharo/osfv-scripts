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

- Flash the BMC flash on an RTE wired to more than one flash chip:

  ```bash
  osfv_cli rte --rte_ip <rte_ip_address> flash write --target bmc --rom <path_to_fw_file>
  ```

  > `--target` is accepted by every `flash` subcommand and by `spi on`, which
  > routes the bus to that flash. It defaults to the first flash the model
  > config lists, and an RTE with a single flash chip only accepts `host`.
  > `spi off` takes no target: it isolates every flash.

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

- `spi_mux`: - optional; true or false (false by default), whether the RTE has
  the SPI mux extension, which routes its SPI bus to one flash at a time. Every
  flash then names the mux branch it sits on, and the RTE closes that branch's
  load switch for the flash it addresses. The extension is an add-on for RTE
  v1.1.0 and later, so it goes with the `rte_1_1` programmer and no other. See
  [SPI mux extension](#spi-mux-extension).

- `gpio`: - optional; pin assignments that differ from the defaults, as
  `<line>: <gpio number>`. What is wired where is a property of the bench, so
  any line can move to another pin on a
  [GPIO header](https://docs.dasharo.com/transparent-validation/rte/v1.1.0/specification/#gpio-header-3).
  Known lines are `relay`, `reset`, `power`, `cmos`, `pwr_led`, `spi_lines`,
  `spi_voltage`, `spi_vcc`, plus `mux_enable`, `mux_select`, `spi_1_power` and
  `spi_2_power` with `spi_mux`. Which ids a line can take follows from how the
  driver drives it, and both ways round are refused: lines driven both high and
  low (`relay`, `pwr_led` and all four mux lines) need a push-pull pin, id 0 or
  13-19, and the rest, which are pulled low and released, need an
  open-collector one, id 1-12. Assigning two lines to one pin, or a name the RTE
  has no such line for, is refused as well.

  ```yaml
  gpio:
    mux_enable: 13
    spi_1_power: 14
    spi_2_power: 15
    mux_select: 16
    pwr_led: 17
  ```

  > The block above spells out the defaults the `spi_mux` driver already uses,
  > which are how a BenchRack is wired; a bench matching it needs no `gpio`
  > block at all.

- `flash_chip`: - the flashes the RTE can reach, at least one. List them
  explicitly, one entry per flash:

    + `target` - required; the name flash commands address this flash by
    (`--target`), e.g. `host` or `bmc`. The first entry is the default.
    + `model` - optional, needs to be set if flashrom detects more than one
    possible flash chip model - in other words, the `-c` parameter you use in
    flashrom.
    + `voltage` - required; chip supply voltage - most often "3.3V" or "1.8V";
    should be discovered in appropriate datasheet.
    + `size` - optional; chip size in bytes. When set, a firmware image of a
    different size is refused instead of flashed.
    + `mux` - required with `spi_mux`; which SPI header the flash is wired to,
    `1` or `2`. A flash that names a branch without `spi_mux` set is refused,
    rather than flashed through whichever branch the mux happens to be on.
    + `power` - optional; true or false (true by default), whether the RTE
    supplies this flash while flashing it. Set it false for a flash its own
    board powers, and neither the SPI Vcc rail nor the flash's load switch is
    touched.

  ```yaml
  spi_mux: true
  flash_chip:
    - target: host
      model: "W25Q256JV_Q"
      voltage: "3.3V"
      size: 33554432
      mux: 1    # connected to the SPI_1 header

    - target: bmc
      voltage: "3.3V"
      size: 67108864
      mux: 2    # connected to the SPI_2 header
  ```

  An RTE with a single flash may instead keep the older mapping form, which
  describes that one flash and needs no `target`; it is addressed as `host`:

  ```yaml
  flash_chip:
    model: "W25Q64JV-.Q"
    voltage: "3.3V"
  ```

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

## SPI mux extension

Most RTEs in the lab are wired to a single DUT flash on their SPI header. An RTE
fitted with the SPI mux extension reaches two, one per SPI header, through a 2:1
SPI mux it drives itself — the arrangement a BenchRack uses to reach both a
host boot flash and a BMC flash. A model config turns it on with `spi_mux: true`
and names the header each flash is wired to. The extension is an add-on PCB for
RTE v1.1.0 and later, so such a config names `rte_1_1` as its programmer;
pairing it with any other is refused as hardware that cannot exist.

Such an RTE differs from a plain one in that:

- Four more lines are driven: the mux enable (active low) and select, and a load
  switch per SPI header. They default to the pins a BenchRack uses — 13, 16, and
  14/15 on the J10 expander header — which is why the power LED readback
  defaults to 17 there rather than 13. The extension goes on a free GPIO header,
  so a bench that wires it elsewhere says so in the model config's `gpio` block.
- A flash operation routes the bus to the flash it addresses (`--target`),
  brings up the SPI Vcc rail, closes that flash's load switch, and isolates both
  flashes again afterward — opening the switch before dropping the rail, so a
  flash is never tied to a de-energized rail another supply may back-drive.
  Every operation parks the bus first, so a run killed part-way through a flash
  cannot leave the RTE driving a flash while the DUT boots.
- The mux select rests on SPI_1 while idle: resting it on SPI_2 holds that
  flash's owner off even with the mux disabled, which on a BenchRack freezes the
  BMC.
- Powering the DUT off for a flash polls the power LED until it is actually off,
  rather than assuming the button press worked.

Everything else is unchanged, including CMOS clear: the extension does not need
the pin a plain RTE clears the CMOS with.

Mains control is unchanged, however it is switched: the smart plug in front of a
BenchRack PSU is a Tasmota device, which is what `pwr_ctrl.sonoff` already
drives.

The GPIO assignment and the flash sequence mirror the `benchrack` driver in
[benchctl](https://git.3mdeb.com/zarhus/benchctl) (`platform/benchrack.go`),
which drives the same extension; keep the two in step when either changes.

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

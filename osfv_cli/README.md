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
  make
  ```

## Usage

1. Customize the configuration:

    > The `~/.osfv/snipeit.yml` should be created automatically upon installing
    > the utility as shown above.

   * Open `~/.osfv/snipeit.yml` and provide your Snipe-IT API URL, API token,
     and user ID
     - `api_url` - typically should be left unchanged, please make sure you have
       correct DNS configuration or entry in `/etc/hosts`,
     - `api_token` - login to Snipe-IT, click on user icon, choose `Manage API
       Keys`, click `Create New Token`, use name `osfv-scripts`, use generated API
       token in config file
     - `user_id` is your Snipe-IT user id, which can be found by going to
       <http://snipeit/users> and showing column ID

To use the script, you can run it with different commands and options. Here are
some examples:

* List all used assets:

  ```shell
  osfv_cli list_used
  ```

* List all unused assets:

  ```shell
  osfv_cli list_unused
  ```

* List all assets:

  ```shell
  osfv_cli list_all
  ```

* Check out an asset (by asset ID):

  ```shell
  osfv_cli check_out --asset_id 123
  ```

* Check in an asset (by asset ID):

  ```shell
  osfv_cli check_in --asset_id 123
  ```

* Check out an asset (by RTE IP):

  ```bash
  osfv_cli check_out --rte_ip <rte_ip_address>
  ```

* Check out an asset (by RTE IP):

  ```bash
  osfv_cli check_out --rte_ip <rte_ip_address>
  ```

  > Replace `<rte_ip_address>` with the actual RTE IP address of the asset you
  > want to check out. The script will identify the asset based on the RTE IP and
  > perform the check-out process.
  > Please note that the RTE IP should match the value stored in the asset's
  > custom field named "RTE IP".

* For more command options, you can use the `--help` flag:

  ```shell
  osfv_cli --help
  ```

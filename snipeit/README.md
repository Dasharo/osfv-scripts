# Snipe-IT Asset Retrieval

This script allows you to interact with Snipe-IT, an open-source asset
management system, via its API. You can use this script to retrieve information
about assets, list used and unused assets, check out and check in assets, and
more.

This script is specific to the OSFV environment and Snipe-IT configuration, and
as such, may not fit for other needs.

## Installation

1. Clone the repository to your local machine:

   ```shell
   git clone https://github.com/dasharo/osfv-scripts.git
   ```

1. Navigate to the cloned repository:

   ```shell
   cd osfv-scripts/snipeit 
   ```

1. Install the necessary dependencies. Make sure you have Python 3 and pip
   installed, then run:

   ```shell
   pip install -r requirements.txt
   ```

1. Install the script and config file template:

    ```shell
    make install
    ```

4. Customize the configuration:

   - Open `~/.osfv/snipeit.yml` and provide your Snipe-IT API URL, API token,
     and user ID

## Usage

To use the script, you can run it with different commands and options. Here are
some examples:

- List all used assets:

  ```shell
  snipeit.py list_used
  ```

- List all unused assets:

  ```shell
  snipeit.py list_unused
  ```

- List all assets:

  ```shell
  snipeit.py list_all
  ```

- Check out an asset (by asset ID):

  ```shell
  snipeit.py check_out --asset_id 123
  ```

- Check in an asset (by asset ID):

  ```shell
  snipeit.py check_in --asset_id 123
  ```

- Check out an asset (by RTE IP):

  ```bash
  snipeit check_out --rte_ip <rte_ip_address>
  ```

- Check out an asset (by RTE IP):

  ```bash
  snipeit check_out --rte_ip <rte_ip_address>
  ```

  > Replace `<rte_ip_address>` with the actual RTE IP address of the asset you
  > want to check out. The script will identify the asset based on the RTE IP and
  > perform the check-out process.
  > Please note that the RTE IP should match the value stored in the asset's
  > custom field named "RTE IP".

- For more command options, you can use the `--help` flag:

  ```shell
  snipeit.py --help
  ```


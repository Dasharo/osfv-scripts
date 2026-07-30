import os
import sys
import time
from pathlib import Path

import yaml
from importlib_resources import files
from osfv.libs.errors import OSFVError
from voluptuous import Any, Optional, Required, Schema


class Models:
    def __init__(self):
        pass

    def list_models(self):
        print(f"Supported DUT models:")
        file_path = os.path.join(files("osfv"), "models")

        for roots, dirs, filenames in os.walk(file_path):
            name_field_len = len(max(filenames, key=len)) + 2
            row_form = "{model_name: <" + str(name_field_len) + "}{status}"
            print(
                row_form.format(
                    model_name="model name", status="configuration file state"
                )
            )
            for file in filenames:
                file_name_body = Path(file).stem
                if self.load_model_data(file_name_body, False)[0]:
                    model_status = "VERIFIED"
                else:
                    model_status = "INCOMPLETE"
                print(
                    row_form.format(
                        model_name=file_name_body, status=model_status
                    )
                )

    def load_model_data(self, dut_model, exit_on_failure=True):
        model_YML_status = True

        file_path = os.path.join(files("osfv"), "models", f"{dut_model}.yml")
        # Check if the file exists
        if not os.path.isfile(file_path):
            if exit_on_failure:
                raise UnsupportedDUTModel(
                    "The {file_path} model is not yet supported".format(
                        file_path=dut_model
                    )
                )
            else:
                model_YML_status = False

        # Load the YAML file
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        voltage_validator = Any("1.8V", "3.3V")
        programmer_name_validator = Any(
            "rte_1_1", "rte_1_0", "ch341a", "dediprog"
        )
        flashing_power_state_validator = Any("G3", "S5")
        pwr_led_validator = Any("active low", "active high")
        layout_schema = [
            {
                Required("name"): str,
                Required("range"): str,
            }
        ]
        # An RTE wired to several flashes lists them explicitly, one entry per
        # flash. An RTE with a single flash may keep the older mapping form,
        # which describes that one flash.
        flash_list_schema = [
            {
                Required("target"): str,
                Required("voltage"): voltage_validator,
                Optional("model"): str,
                Optional("size"): int,
                Optional("mux"): int,
                Optional("power"): bool,
                Optional("layout"): layout_schema,
            }
        ]
        flash_mapping_schema = {
            Required("voltage"): voltage_validator,
            Optional("model"): str,
            Optional("size"): int,
            Optional("layout"): layout_schema,
        }

        # Pin assignments a bench may override. Which pin a line is wired to is
        # a property of the bench, so the driver validates the names and ids it
        # knows; the schema only checks the shape.
        gpio_schema = {str: int}

        schema = Schema(
            {
                Optional("spi_mux"): bool,
                Optional("gpio"): gpio_schema,
                Required("programmer"): {
                    Required("name"): programmer_name_validator,
                },
                Required("flash_chip"): Any(
                    flash_list_schema, flash_mapping_schema
                ),
                Required("pwr_ctrl"): {
                    Required("sonoff"): bool,
                    Required("relay"): bool,
                    Required(
                        "flashing_power_state"
                    ): flashing_power_state_validator,
                    Optional("discharge_psu", default=True): bool,
                },
                Optional("pwr_led"): {
                    Required("polarity"): pwr_led_validator,
                },
                Optional("reset_cmos", default=False): bool,
                Optional("disable_wp", default=False): bool,
            }
        )

        try:
            schema(data)
        except Exception as e:
            if exit_on_failure:
                exit(f"Model file is invalid: {e}")
            else:
                model_YML_status = False

        # Check if required fields are present
        required_fields = [
            "pwr_ctrl",
            "pwr_ctrl.sonoff",
            "pwr_ctrl.relay",
            "flash_chip",
            "programmer",
            "programmer.name",
        ]
        # The mapping form keeps voltage directly under flash_chip; the list
        # form carries one per flash, checked by the schema above.
        if isinstance(data.get("flash_chip"), dict):
            required_fields.append("flash_chip.voltage")
        for field in required_fields:
            current_field = data
            keys = field.split(".")
            for key in keys:
                if key in current_field:
                    current_field = current_field[key]
                else:
                    if exit_on_failure:
                        exit(
                            f"Required field '{field}' is missing in model "
                            f"config."
                        )
                    else:
                        model_YML_status = False

        # Return the loaded data
        return model_YML_status, data

    def flash_targets(self, dut_data):
        """
        Returns the flashes an RTE can address, keyed by target name in the
        order the model config lists them, so the first one is the default.

        Both `flash_chip` forms normalize to the same shape: a list of explicit
        flashes keeps its `target` names, and the single-flash mapping form
        becomes one target named `host`.

        Args:
            dut_data (dict): The loaded model config.

        Returns:
            dict: Target name to its flash configuration.

        Raises:
            DuplicateFlashTarget: If two entries name the same target.
        """
        flash_chip = dut_data.get("flash_chip", {})
        if isinstance(flash_chip, dict):
            return {DEFAULT_FLASH_TARGET: dict(flash_chip)}

        targets = {}
        for flash in flash_chip:
            flash = dict(flash)
            name = flash.pop("target")
            if name in targets:
                raise DuplicateFlashTarget(
                    f"Model config lists the '{name}' flash more than once"
                )
            targets[name] = flash
        return targets


# Name given to the flash of a model config written in the single-flash mapping
# form, which does not name its flash.
DEFAULT_FLASH_TARGET = "host"


class IncompleteModelData(OSFVError):
    pass


class DuplicateFlashTarget(OSFVError):
    pass


class UnsupportedDUTModel(OSFVError):
    pass

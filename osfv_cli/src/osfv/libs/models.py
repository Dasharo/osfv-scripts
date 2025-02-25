import os
import sys
import time
from pathlib import Path

import yaml
from importlib_resources import files
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
                    if exit_on_failure:
                        exit(
                            f"Required field '{field}' is missing in model "
                            f"config."
                        )
                    else:
                        model_YML_status = False

        # Return the loaded data
        return model_YML_status, data


class IncompleteModelData(Exception):
    pass


class UnsupportedDUTModel(Exception):
    pass

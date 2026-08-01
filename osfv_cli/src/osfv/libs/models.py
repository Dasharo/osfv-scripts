from pathlib import PurePath

import yaml
from importlib_resources import files
from pydantic_core import ValidationError

from osfv.libs.models_gen import FlashingConfiguration


class Models:
    def __init__(self):
        pass

    def list_models(self):
        print("Supported DUT models:")
        file_path = files("osfv") / "models"

        name_field_len = (
            len(max(file_path.iterdir(), key=lambda path: len(path.name)).name)
            + 2
        )
        row_form = f"{{model_name: <{name_field_len}}}{{status}}"
        print(
            row_form.format(
                model_name="model name", status="configuration file state"
            )
        )
        for filename in file_path.iterdir():
            if not filename.is_file():
                continue
            file_name_body = PurePath(filename.name).stem
            model_status = "INCOMPLETE"
            try:
                self.load_model_data(file_name_body)
                model_status = "VERIFIED"
            except (UnsupportedDUTModel, ValidationError):
                pass
            print(
                row_form.format(model_name=file_name_body, status=model_status)
            )

    def load_model_data(self, dut_model: str) -> FlashingConfiguration:
        """Load the DUT YAML model and return typed Python object

        Args:
            dut_model (str): name of the DUT model

        Raises:
            UnsupportedDUTModel: No YAML model for DUT exists
            ValidationError: Loaded YAML model failed to validate

        Returns:
            FlashingConfiguration: loaded model
        """
        file_path = files("osfv") / "models" / f"{dut_model}.yml"
        # Check if the file exists
        if not file_path.is_file():
            raise UnsupportedDUTModel(
                f"The {dut_model} model is not yet supported"
            )

        # Load the YAML file
        with file_path.open("r") as file:
            data = yaml.safe_load(file)

        return FlashingConfiguration(**data)


class UnsupportedDUTModel(Exception):
    pass

import os
import struct
import sys
from itertools import repeat


class FlashImage:
    # based on flashrom/utils/ich_descriptor_tool.c
    REGION_INDICES = [
        "fd",
        "bios",
        "me",
        "gbe",
        "pd",
        "reg5",
        "bios2",
        "reg7",
        "ec",
        "reg9",
        "ie",
        "10gbe",
        "reg12",
        "reg13",
        "reg14",
        "reg15",
    ]
    NUMBER_OF_REGIONS = len(REGION_INDICES)
    FLVALSIG = 0x0FF0A55A

    def set_verbosity(self, verbosity):
        self.VERBOSITY = verbosity

    def get_verbosity(self):
        return self.VERBOSITY

    def set_exit_code(self, exit_code):
        self.EXIT_CODE = exit_code

    def get_exit_code(self):
        return self.EXIT_CODE

    def get_image_data(self):
        return imageData

    def get_region_index(self, region_name):
        try:
            region_index = self.REGION_INDICES.index(region_name)
        except ValueError:
            print('FAILURE: Unknown flash region: "' + region_name + '"')
            self.EXIT_CODE = 1
            region_index = None
        return region_index

    def get_known_regions_list(self):
        return self.REGION_INDICES

    def __init__(self):
        self.set_exit_code(0)
        self.set_verbosity(0)

    def load_image_file(self, image_path):
        if not os.path.isfile(image_path):
            print(f"File does not exist: {image_path}")
            self.EXIT_CODE = False
            return False
        with open(
            image_path,
            mode="rb",
        ) as imageFile:
            self.imageData = imageFile.read()
            valsig = struct.unpack("<I", self.imageData[0x00:0x04])[0x0]
            valsig_offset = 0x00
            if valsig != self.FLVALSIG:
                valsig_offset = 0x10
                valsig = struct.unpack(
                    "<I",
                    self.imageData[valsig_offset : (valsig_offset + 0x04)],
                )[0x00]
                if valsig != self.FLVALSIG:
                    print("Invalid image, no FLVALSIG found!")
                    self.EXIT_CODE = False
                    return False
            if self.VERBOSITY > 0:
                print("FLVALSIG: {0:#0{1}x}".format(valsig, 0x0A))

            FLMAP0 = struct.unpack(
                "<I",
                self.imageData[
                    (valsig_offset + 0x04) : (valsig_offset + 0x08)
                ],
            )[0x00]
            FRBA = (FLMAP0 >> 0x0C) & 0x00000FF0

            if self.VERBOSITY > 0:
                print("FLMAP0: {0:#0{1}x}".format(FLMAP0, 0x0A))
                print("FRBA: {0:#0{1}x}".format(FRBA, 0x06))

            region_format = f"<{self.NUMBER_OF_REGIONS}I"
            self.REGIONS = struct.unpack(
                region_format,
                self.imageData[
                    FRBA : (FRBA + (0x04 * self.NUMBER_OF_REGIONS))
                ],
            )
            return True

    def get_region_data(self, pIndex, pName):
        if self.REGIONS[pIndex] == 0x00007FFF:
            print(
                'FAILURE: Region "'
                + pName
                + '" at index '
                + str(pIndex)
                + " is empty!"
            )
            return None
        reg_base = (self.REGIONS[pIndex] << 12) & 0x07FFF000
        reg_limit = ((self.REGIONS[pIndex] >> 4) & 0x07FFF000) | 0x00000FFF

        if self.VERBOSITY > 0:
            print(
                pName + "_FLREG: {0:#0{1}x}".format(self.REGIONS[pIndex], 0x0A)
            )
            print(pName + "_BASE: {0:#0{1}x}".format(reg_base, 0x0A))
            print(pName + "_LIMIT: {0:#0{1}x}".format(reg_limit, 0x0A))

        reg_data = self.imageData[reg_base : (reg_limit + 0x01)]
        return reg_data

    def check_region(self, pIndex, pName):
        reg_data = self.get_region_data(pIndex, pName)
        if reg_data != None:
            iterator = list(repeat(reg_data[0], len(reg_data)))
            if iterator == reg_data:
                print(
                    "FAILURE: Invalid region content, filled with: {0:#0{1}x}".format(
                        reg_data[0], 0x04
                    )
                )
                self.EXIT_CODE = 1
            print(
                f'SUCCESS: region "{pName}" is present and contains some data.'
            )
        else:
            if self.VERBOSITY > 0:
                print("FAILURE: region data access failed.")
            self.EXIT_CODE = 1

    def dump_region(self, pIndex, pName):
        reg_data = self.get_region_data(pIndex, pName)
        if reg_data != None:
            with open(pName + "_dump.bin", mode="wb") as meFile:
                meFile.write(reg_data)
            print('Region "' + pName + '" dumped to: ' + pName + "_dump.bin")
        else:
            if self.VERBOSITY > 0:
                print("Region dump failed.")
            self.EXIT_CODE = 1

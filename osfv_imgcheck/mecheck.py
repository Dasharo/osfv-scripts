#!/usr/bin/env python3

import argparse
import struct
import sys
from itertools import repeat

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


def get_region_data(pIndex, pName):
    if REGIONS[pIndex] == 0x00007FFF:
        print('Region "' + pName + '" at index ' + str(pIndex) + " is empty!")
        return None
    reg_base = (REGIONS[pIndex] << 12) & 0x07FFF000
    reg_limit = ((REGIONS[pIndex] >> 4) & 0x07FFF000) | 0x00000FFF

    # if
    print(pName + "_FLREG: {0:#0{1}x}".format(REGIONS[pIndex], 0x0A))
    print(pName + "_BASE: {0:#0{1}x}".format(reg_base, 0x0A))
    print(pName + "_LIMIT: {0:#0{1}x}".format(reg_limit, 0x0A))

    reg_data = imageData[reg_base : (reg_limit + 0x01)]
    return reg_data


def check_region(pIndex, pName):
    reg_data = get_region_data(pIndex, pName)
    if reg_data != None:
        iterator = list(repeat(reg_data[0], len(reg_data)))
        if iterator == reg_data:
            print(
                "Invalid region content, filled with: {0:#0{1}x}".format(
                    reg_data[0], 0x04
                )
            )


def dump_region(pIndex, pName):
    # try
    reg_data = get_region_data(pIndex, pName)
    if reg_data != None:
        with open(pName + "_dump.bin", mode="wb") as meFile:
            meFile.write(reg_data)
        print('Region "' + pName + '" dumped to: ' + pName + "_dump.bin")


def main():
    global REGIONS, imageData, VERBOSITY

    VERBOSITY = 0x00

    parser = argparse.ArgumentParser(description="Dasharo flash image MEcheck")
    parser.add_argument(
        "-v",
        "--verbosity",
        help="increase output verbosity (0 or 1)",
        action="append",
        type=int,
    )
    parser.add_argument(
        "-l",
        "--list",
        help="list known region names",
        action="store_true",
        dest="list",
    )
    parser.add_argument(
        "flash_image_file", nargs="?", default=None, help="flash image file"
    )
    parser.add_argument(
        "-c",
        "--check",
        help="check named flash region",
        action="append",
        type=str,
        dest="region_to_check",
    )
    parser.add_argument(
        "-d",
        "--dump",
        help="dump named flash region",
        action="append",
        type=str,
        dest="region_to_dump",
    )
    parser.add_argument(
        "-x",
        "--dry",
        help="failed region checks won't change exit status",
        action="store_true",
        dest="dry",
    )

    args = parser.parse_args()
    if args.verbosity:
        print("verbosity changed to: " + str(args.verbosity))
        VERBOSITY = args.verbosity
    if args.list:
        print("Known regions:")
        for reg_name in REGION_INDICES:
            print(reg_name)
        sys.exit(0)
    if args.flash_image_file:
        with open(
            args.flash_image_file,
            mode="rb",
        ) as imageFile:
            imageData = imageFile.read()
            valsig = struct.unpack("<I", imageData[0x00:0x04])[0x0]
            valsig_offset = 0x00
            if valsig != FLVALSIG:
                valsig_offset = 0x10
                valsig = struct.unpack(
                    "<I", imageData[valsig_offset : (valsig_offset + 0x04)]
                )[0x0]
                if valsig != FLVALSIG:
                    sys.exit("Invalid image, no FLVALSIG found!")
            print("FLVALSIG: {0:#0{1}x}".format(valsig, 0x0A))

            FLMAP0 = struct.unpack(
                "<I",
                imageData[(valsig_offset + 0x04) : (valsig_offset + 0x08)],
            )[0x00]
            print("FLMAP0: {0:#0{1}x}".format(FLMAP0, 0x0A))

            FRBA = (FLMAP0 >> 0x0C) & 0x00000FF0
            print("FRBA: {0:#0{1}x}".format(FRBA, 0x06))

            region_format = f"<{NUMBER_OF_REGIONS}I"
            REGIONS = struct.unpack(
                region_format,
                imageData[FRBA : (FRBA + (0x04 * NUMBER_OF_REGIONS))],
            )
    if args.region_to_check:
        for check_region_name in args.region_to_check:
            try:
                check_region_index = REGION_INDICES.index(check_region_name)
            except ValueError:
                sys.exit("Unsupported flash region: " + check_region_name)
            check_region(check_region_index, check_region_name)
    if args.region_to_dump:
        for dump_region_name in args.region_to_dump:
            try:
                dump_region_index = REGION_INDICES.index(dump_region_name)
            except ValueError:
                sys.exit("Unsupported flash region: " + dump_region_name)
            dump_region(dump_region_index, dump_region_name)


if __name__ == "__main__":
    main()

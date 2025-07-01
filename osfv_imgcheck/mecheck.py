#!/usr/bin/env python3

import argparse
import pathlib
import struct

NUMBER_OF_REGIONS = 0x10
BIOS_REGION_INDEX = 0x01
ME_REGION_INDEX = 0x02


def dump_region(pIndex, pName):
    reg_base = (REGIONS[pIndex] << 12) & 0x07FFF000
    reg_limit = ((REGIONS[pIndex] >> 4) & 0x07FFF000) | 0x00000FFF

    print(pName + "_FLREG: {0:#0{1}x}".format(REGIONS[pIndex], 0x0A))
    print(pName + "_BASE: {0:#0{1}x}".format(reg_base, 0x0A))
    print(pName + "_LIMIT: {0:#0{1}x}".format(reg_limit, 0x0A))

    reg_data = imageData[reg_base : (reg_limit + 0x01)]
    with open(pName + "_dump.bin", mode="wb") as meFile:
        meFile.write(reg_data)


def main():
    parser = argparse.ArgumentParser(description="Dasharo flash image MEcheck")
    parser.add_argument("flash_image_file")
    parser.add_argument("-v", "--verbosity", help="increase output verbosity")
    parser.add_argument(
        "-d",
        "--dump",
        help="dump named flash region",
        action="append",
        type=str,
    )
    args = parser.parse_args()
    if args.verbosity:
        print("verbosity turned on" + str(args.verbosity))
    if args.flash_image_file:
        with open(
            args.flash_image_file,
            mode="rb",
        ) as imageFile:
            imageData = imageFile.read()
            FLMAP0 = struct.unpack("<I", imageData[0x04:0x08])[0x00]
            print(hex(FLMAP0))

            FRBA = (FLMAP0 >> 0x04) & 0x00000FF0
            print("FRBA: {0:#0{1}x}".format(FRBA, 0x06))

            region_format = f"<{NUMBER_OF_REGIONS}I"
            REGIONS = struct.unpack(
                region_format,
                imageData[FRBA : (FRBA + (0x04 * NUMBER_OF_REGIONS))],
            )
    if args.dump:
        print(args.dump)
        dump_region(ME_REGION_INDEX, "ME")
        dump_region(BIOS_REGION_INDEX, "BIOS")


if __name__ == "__main__":
    main()

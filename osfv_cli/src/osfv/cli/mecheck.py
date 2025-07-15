#!/usr/bin/env python3

import argparse
import sys

from osfv.libs.flash_image import FlashImage


def main():
    flash_image = FlashImage()

    parser = argparse.ArgumentParser(description="Dasharo flash image MEcheck")
    parser.add_argument(
        "-v",
        "--verbosity",
        help="increase output verbosity",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--list",
        help="list known region names and exit",
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
        "--dry-run",
        help="failed region checks won't change exit status",
        action="store_true",
        dest="dry",
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    args = parser.parse_args()
    if args.verbosity:
        print("Verbosity increased.")
        flash_image.set_verbosity(1)
    if args.list:
        print("Known regions:")
        for reg_name in flash_image.get_known_regions_list():
            print(reg_name)
        sys.exit(0)
    if args.flash_image_file:
        flash_image.load_image_file(args.flash_image_file)
    else:
        print(f"FATAL: flash image file name not provided.")
        sys.exit(1)
    if args.region_to_check:
        for check_region_name in args.region_to_check:
            check_region_index = flash_image.get_region_index(
                check_region_name
            )
            if check_region_index == None:
                continue
            flash_image.check_region(check_region_index, check_region_name)
    if args.region_to_dump:
        for dump_region_name in args.region_to_dump:
            dump_region_index = flash_image.get_region_index(dump_region_name)
            if dump_region_index == None:
                continue
            flash_image.dump_region(dump_region_index, dump_region_name)
    if args.dry:
        if flash_image.get_verbosity() > 0:
            print("WARNING: this is dry run with exit status overridden.")
        flash_image.set_exit_code(0)
    sys.exit(flash_image.get_exit_code())


if __name__ == "__main__":
    main()

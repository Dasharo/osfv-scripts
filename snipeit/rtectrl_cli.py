#!/usr/bin/env python3

import argparse
from rtectrl_api import RTE

# Create an instance of the RTE class with the RTE IP
rte = RTE("192.168.10.233")


def power_on(args):
    rte.power_on(args.time)


def power_off(args):
    rte.power_off(args.time)


def reset(args):
    rte.reset(args.time)

def get_gpio_state(args):
    state = rte.gpio_get(args.gpio_no)
    print(f"GPIO {args.gpio_no} state: {state}")


def set_gpio_state(args):
    rte.gpio_set(args.gpio_no, args.state)
    print(f"GPIO {args.gpio_no} state set to {args.state}")


def relay_toggle(args):
    rte.relay_toggle()
    state = rte.relay_get()
    print(f"Relay state toggled. New state: {state}")

def relay_set(args):
    rte.relay_set(args.state)
    print(f"Relay state set to {args.state}")

def relay_get():
    state = rte.relay_get()
    print(f"Relay state: {state}")


def main():
    parser = argparse.ArgumentParser(prog="rte_ctrl")
    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    # Power subcommands
    power_parser = subparsers.add_parser("power", help="Power control commands")
    power_subparsers = power_parser.add_subparsers(title="subcommands", dest="power_command")
    power_on_parser = power_subparsers.add_parser("on", help="Power on")
    power_on_parser.add_argument("--time", type=int, default=1, help="Time in seconds (default: 1)")
    power_off_parser = power_subparsers.add_parser("off", help="Power off")
    power_off_parser.add_argument("--time", type=int, default=5, help="Time in seconds (default: 5)")
    reset_parser = power_subparsers.add_parser("reset", help="Reset")
    reset_parser.add_argument("--time", type=int, default=1, help="Time in seconds (default: 1)")

    # GPIO subcommands
    gpio_parser = subparsers.add_parser("gpio", help="GPIO commands")
    gpio_subparsers = gpio_parser.add_subparsers(title="subcommands", dest="gpio_command")
    get_gpio_parser = gpio_subparsers.add_parser("get", help="Get GPIO state")
    get_gpio_parser.add_argument("gpio_no", type=int, help="GPIO number")
    set_gpio_parser = gpio_subparsers.add_parser("set", help="Set GPIO state")
    set_gpio_parser.add_argument("gpio_no", type=int, help="GPIO number")
    set_gpio_parser.add_argument("state", choices=["high", "low", "high-z"], help="GPIO state")

    # OC GPIO subcommands
    oc_gpio_parser = subparsers.add_parser("oc_gpio", help="OC GPIO commands")
    oc_gpio_subparsers = oc_gpio_parser.add_subparsers(title="subcommands", dest="oc_gpio_command")

    # Relay subcommands
    relay_parser = subparsers.add_parser("relay", help="Relay commands")
    relay_subparsers = relay_parser.add_subparsers(title="subcommands", dest="relay_command")
    toggle_relay_parser = relay_subparsers.add_parser("toggle", help="Toggle relay state")
    get_relay_parser = relay_subparsers.add_parser("get", help="Get relay state")
    set_relay_parser = relay_subparsers.add_parser("state", help="Set relay state")
    set_relay_parser.add_argument("state", choices=["high", "low",], help="GPIO state")

    args = parser.parse_args()

    if args.subcommand == "power":
        if args.power_command == "on":
            power_on(args)
        elif args.power_command == "off":
            power_off(args)
        elif args.power_command == "reset":
            reset(args)
    elif args.subcommand == "gpio":
        if args.gpio_command == "get":
            get_gpio_state(args)
        elif args.gpio_command == "set":
            set_gpio_state(args)
    elif args.subcommand == "relay":
        if args.relay_command == "toggle":
            relay_toggle()
        elif args.relay_command == "get":
            relay_get()
        elif args.relay_command == "set":
            relay_set(args)

if __name__ == "__main__":
    main()

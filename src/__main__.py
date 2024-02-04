#!/bin/env python

"""Script to prevent server going to sleep when there are active clients.

Supports checking for ssh and nfs clients.
Uses dbus to prevent sleep.
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import Sequence

from . import __version__
from .prevent_sleep import prevent_sleep
from .install_service import install_service


_LOG = logging.getLogger(__name__)
_LOG_STREAM = sys.stdout


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command line arguments return validated and converted args."""
    parser = argparse.ArgumentParser(
        prog=Path(argv[0]).name,
        description="Prevent server from going to sleep/suspend when there are active SSH or NFS connections.",
        epilog="")
    parser.add_argument("--sleep-seconds", type=int, default=10, help="Time to sleep between each check.")
    parser.add_argument("--max-inactive-seconds", type=int, default=120, help="Time delay uninhibit after laste checker requested inhibit.")
    parser.add_argument("--loglevel", help="Name of a Python logging loglevel. E.g.: 'debug'. The default loglevel is 'INFO'")
    parser.add_argument("--install-service", action='store_true', help="Install the systemd service")
    parser.add_argument('-V', '--version', action='store_true', help="Program version.")
    args = parser.parse_args(argv[1:])

    loglevel = logging.INFO
    if args.loglevel:
        try:
            loglevel = getattr(logging, args.loglevel.upper())
            loglevel = int(loglevel)
        except (AttributeError, ValueError, TypeError) as ex:
            msg = f"Invalid loglevel: {args.loglevel} {ex}"
            if _LOG_STREAM != sys.stdout:
                _LOG.error(msg)
            if _LOG_STREAM != sys.stderr:
                print(msg, file=sys.stderr)
            sys.exit(1)

    args.loglevel = loglevel
    return args


def cli(argv: Sequence[str] = sys.argv):
    """Parse command line arguments and run program."""
    args = parse_args(argv)

    logging.basicConfig(level=args.loglevel, format='%(message)s', stream=_LOG_STREAM)

    if args.version:
        prog_name = argv[0]
        msg = f"{prog_name} {__version__}"
        if _LOG_STREAM not in [sys.stdout, sys.stderr]:
            _LOG.info(msg)
        print(msg)
        return

    if args.install_service:
        install_service()
        return

    prevent_sleep(args.loglevel, args.sleep_seconds, args.max_inactive_seconds)


if __name__ == "__main__":
    cli()

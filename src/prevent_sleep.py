"""Prevent server going to sleep when there are active clients.

Supports checking for SSH and NFS clients.
Uses dbus to prevent sleep.
"""

import os
import importlib
import time
from pathlib import Path
from datetime import datetime, timedelta
import logging

from .checks.checker import Checker
from .inhibitors.dbus_inhibit import DbusInhibit
from .inhibitors.systemd_mask import SystemdMaskManager

_HERE = Path(__file__).parent
_LOG = logging.getLogger(__name__)


class CheckInhibit():
    """Perform checks and inhibit sleep is there are active clients.

    Remove inhibit after a delay when clients become inactive or disappear.
    """

    def __init__(self, checker: Checker, max_inactive_seconds: int):
        self.checker = checker
        self.inhibitor = DbusInhibit(checker.name)
        self.max_inactive_seconds = max_inactive_seconds
        self.last_active_time = None

    def check_and_inhibit(self):
        """Execute checker and inhibit sleep if checker returns a non-empty str."""
        td_max_inactive = timedelta(seconds=self.max_inactive_seconds)
        why = self.checker.check()

        if why:
            self.last_active_time = datetime.now()
            return self.inhibitor.inhibit(why)

        if self.last_active_time:
            time_since_last_active = datetime.now() - self.last_active_time
            if time_since_last_active > td_max_inactive:
                _LOG.info("No activity for %s which is more than max time %s. Removing block.", time_since_last_active, td_max_inactive)
                return self.inhibitor.uninhibit()

            _LOG.debug("Time since last activity %s which is less than max time %s", time_since_last_active, td_max_inactive)
            remove_time = (self.last_active_time + td_max_inactive).isoformat(timespec='seconds')
            return self.inhibitor.inhibit(f"No activity. Will remove block at {remove_time}")

        return False


def prevent_sleep(loglevel, check_interval_seconds = 10, max_inactive_seconds = 120, max_loops = 0):
    """Loop and execute checks/inhibits."""
    _LOG.info("Starting prevent-sleep")

    euid = os.geteuid()
    _LOG.debug("euid: %s", euid)
    if euid:
        _LOG.warning("Program is not running as root. Functionality will be limited.")

    check_inhibitors = []
    _LOG.info("")
    for ff in os.scandir(_HERE/"checks"):
        if not ff.name.endswith(".py") or ff.name in ["__init__.py", "checker.py"]:
            continue
        mod = importlib.import_module(".checks." + Path(ff).stem, package="prevent_sleep")
        checker = mod.Checker(check_interval_seconds)
        _LOG.info("Imported checker '%s', from: %s", checker.name, ff.path)
        check_inhibitors.append(CheckInhibit(checker, max_inactive_seconds))
    _LOG.info("")

    # For logging
    _ = SystemdMaskManager()
    _LOG.info("")

    loop_num = 0
    logging.getLogger().setLevel(logging.DEBUG)  # Log first loop at debug level.
    while not max_loops or loop_num < max_loops:
        for check_inhibitor in check_inhibitors:
            check_inhibitor.check_and_inhibit()

        _LOG.log(logging.DEBUG, "Sleeping %s seconds.\n", check_interval_seconds)
        if loop_num == 0:
            logging.getLogger().setLevel(loglevel)
            if loglevel >= logging.INFO:
                # Don't log this at DEBUG because it will be incorrect!
                _LOG.info("Will only log if state changes from now on.\n")

        loop_num += 1
        time.sleep(check_interval_seconds)

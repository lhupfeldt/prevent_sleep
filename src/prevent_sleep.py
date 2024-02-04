"""Prevent server going to sleep when there are active clients.

Supports checking for SSH and NFS clients.
Uses dbus to prevent sleep.
"""

import os
import time
from datetime import datetime, timedelta
import logging

from .checks.checker import Checker
from .checks.ssh_clients import SshChecker
from .checks.nfs_clients import NfsChecker
from .inhibitors.dbus_inhibit import DbusInhibit

_LOG = logging.getLogger(__name__)


class CheckInhibit():
    """Perform checks and inhibit sleep is there are active clients.

    Remove inhibit after a delay when clients become inactive or disappear.
    """

    def __init__(self, checker: Checker, inhibitor: DbusInhibit, max_inactive_seconds: int):
        self.checker = checker
        self.inhibitor = inhibitor
        self.max_inactive_seconds = max_inactive_seconds
        self.prev_why = None
        self.last_active_time = None

    def check_and_inhibit(self, loop_num):
        """Execute checker and inhibit sleep if checker returns a non-empty str."""
        td_max_inactive = timedelta(seconds=self.max_inactive_seconds)
        why = self.checker.check()

        if why:
            self.last_active_time = datetime.now()
            return self.inhibitor.inhibit(why)

        if self.last_active_time:
            time_since_last_active = datetime.now() - self.last_active_time
            if time_since_last_active > td_max_inactive:
                _LOG.log(
                    logging.INFO if self.prev_why or loop_num == 0 else logging.DEBUG,
                    "No activity for %s which is more than max time %s. Removing block.", time_since_last_active, td_max_inactive)
                return self.inhibitor.uninhibit()

            _LOG.debug("Time since last activity %s which is less than max time %s", time_since_last_active, td_max_inactive)
            remove_time = (self.last_active_time + td_max_inactive).isoformat(timespec='seconds')
            return self.inhibitor.inhibit(f"No activity. Will remove block at {remove_time}")

        _LOG.debug("No activity")
        return False


def prevent_sleep(loglevel, sleep_seconds = 10, max_inactive_seconds = 120, max_loops = 0):
    """Loop and execute checks/inhibits."""
    _LOG.info("Starting prevent-sleep")

    euid = os.geteuid()
    _LOG.debug("euid: %s", euid)
    if euid:
        _LOG.warning("Program is not running as root. Functionality will be limited.")

    ssh_ci = CheckInhibit(SshChecker(sleep_seconds), DbusInhibit("SSH"), max_inactive_seconds)
    nfs_ci = CheckInhibit(NfsChecker(sleep_seconds), DbusInhibit("NFS"), max_inactive_seconds)

    loop_num = 0
    while not max_loops or loop_num < max_loops:
        change = ssh_ci.check_and_inhibit(loop_num) or loop_num == 0  # Always log the first loop
        change = nfs_ci.check_and_inhibit(loop_num) or change
        _LOG.log(logging.INFO if change else logging.DEBUG, "Sleeping %s seconds.\n", sleep_seconds)
        if loglevel >= logging.INFO and loop_num == 0:
            # Don't log this at DEBUG because it will be incorrect!
            _LOG.info("Will only log if state changes from now on\n")

        loop_num += 1
        time.sleep(sleep_seconds)

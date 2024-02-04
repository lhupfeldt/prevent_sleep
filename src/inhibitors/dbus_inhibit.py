"""Use D-Bus to inhibit sleep/suspend

See:
https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html
https://gitlab.freedesktop.org/dbus/dbus-python.git
"""

# requires: dbus-python

import os
import logging
from typing import ClassVar

import dbus  # type: ignore

from .systemd_mask import SystemdMaskManager


_LOG = logging.getLogger(__name__)


class DBusProxy():  # pylint: disable=too-few-public-methods
    """There should be only one instantiation."""
    def __init__(self):
        system_bus = dbus.SystemBus()
        _LOG.debug("D-Bus system bus: %s", system_bus)
        self.proxy = system_bus.get_object('org.freedesktop.login1', "/org/freedesktop/login1")
        _LOG.debug("D-Bus object proxy %s", self.proxy)
        _ = SystemdMaskManager()


class DbusInhibit():
    """Remember state so that we can limit logging to changes."""
    proxy: ClassVar[DBusProxy] = None  # type: ignore[assignment]

    def __init__(self, name: str):
        """Inhibit sleep/suspend using D-Bus.

        Arguments:
        name: The name of this inhibitor, e.g. SSH or NFS
        dbus_proxy: The dbus proxy.
        """

        self.who: str = "prevent-sleep"
        self.name = name
        self.inhibit_fd = None
        self.why = ""

        if not self.proxy:
            self.__class__.proxy = DBusProxy()

    def _uninhibit(self, inhibit_fd: int):
        """Return open file descriptor which must be closed to remove inhibit."""
        _LOG.debug("%s: Close inhibit filehandle %s", self.name, self.inhibit_fd)
        os.close(inhibit_fd)

    def inhibit(self, why: str):
        """Call D-Bus inhibit and save file descriptor."""
        if self.why != why:
            _LOG.info("%s: Calling dbus inhibit to prevent sleep/suspend: %s %s", self.name, self.who, why)
            prev_inhibit_fd = self.inhibit_fd
            self.inhibit_fd = self.proxy.proxy.Inhibit("sleep", self.who, f"{self.name}: {why}", "block", dbus_interface="org.freedesktop.login1.Manager").take()
            _LOG.debug("%s: Inhibit file handle: %s", self.name, self.inhibit_fd)
            if prev_inhibit_fd:
                self._uninhibit(prev_inhibit_fd)
            self.why = why
            return True

        _LOG.debug("%s: Sleep is already inhibited for same reason %s - nothing to do", self.name, why)
        return False

    def uninhibit(self):
        """Return open file descriptor which must be closed to remove inhibit."""
        if self.inhibit_fd is not None:
            _LOG.info("%s: Removing dbus sleep/suspend inhibit", self.name)
            self._uninhibit(self.inhibit_fd)
            self.inhibit_fd = None
            self.why = None
            return True

        _LOG.debug("%s: Sleep was not inhibited - nothing to do.", self.name)
        return False

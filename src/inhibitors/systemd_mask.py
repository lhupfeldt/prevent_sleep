"""Report systemd sleep related unit states."""

# Requires pystemd
# sudo dnf install python3-pystemd - to get system dependencies

import atexit
import logging

from pystemd.systemd1 import Unit  # type: ignore
from pystemd.systemd1 import Manager  # type: ignore


_LOG = logging.getLogger(__name__)


class SystemdMaskManager():  # pylint: disable=too-few-public-methods
    """Log whether systemd sleep related units are masked."""
    def __init__(self):
        self.unit_names = [b"sleep.target", b"suspend.target", b"hibernate.target", b"hybrid-sleep.target"]
        _LOG.info("Systemd units for sleep/suspend %s", self.unit_names)

        self.units = [Unit(unit_name) for unit_name in self.unit_names]

        self.manager = Manager()
        self.manager.load()

        for unit in self.units:
            unit.load()

        self._pstates(logging.INFO, "Unit states")
        self.masked = False  # Assumption

        atexit.register(self._pstates, logging.WARNING, "Exit")

    def _pstates(self, loglevel, msg: str):
        _LOG.log(loglevel, "%s. Systemd unit states:", msg)
        for unit in self.units:
            _LOG.log(
                loglevel,
                "%s, %s, %s, %s",
                unit.external_id, unit.Unit.ActiveState, unit.Unit.LoadState, unit.Unit.UnitFileState)

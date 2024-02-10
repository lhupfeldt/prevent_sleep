"""Check for (active) ssh clients."""

# Tested on Fedora 39
# Requires psutil

import logging

import psutil

from . import checker


_LOG = logging.getLogger(__name__)


class Checker(checker.Checker):
    """Check for *active* SSH clients."""
    def __init__(self, check_interval_seconds: int, max_read_chars_per_second: int = 20):
        super().__init__(check_interval_seconds=check_interval_seconds)
        self.max_read_chars = max_read_chars_per_second * check_interval_seconds
        self.clients: dict[int, tuple[int, bool, str]] = {}  # pid -> read_chars, active, username

    @property
    def name(self):
        return "SSH"

    def check(self) -> str:
        """Return non-empty str with info if any active ssh connections are found.

        Most important info should be at start of return value, it may be truncated in D-Bus messsage.
        """

        prev_clients = self.clients
        prev_active_clients = False
        self.clients = {}
        active_clients = []

        for proc in psutil.process_iter(["pid", "name", "username", "io_counters"]):
            # info = proc.as_dict()
            info = proc.info  # type: ignore
            username = info["username"]

            if info["name"] == "sshd" and username not in ["root", "sshd"]:
                _LOG.debug("%s: %s", self.name, info)
                pid = info["pid"]

                prev_read_chars, prev_active, _ = prev_clients.get(pid, (0, False, ""))
                prev_active_clients = prev_active_clients or prev_active

                try:
                    read_chars = info["io_counters"].read_chars
                    read_since_last = read_chars - prev_read_chars
                    active = read_since_last > self.max_read_chars
                except AttributeError as ex:
                    _LOG.warning("%s: Must run as root to determine if session is active. Assuming all sessions active. %s.", self.name, ex)
                    read_chars = 0
                    active = True

                self.clients[pid] = read_chars, active, username

                if active:
                    level = logging.INFO if not prev_active else logging.DEBUG
                    if read_chars:
                        _LOG.log(
                            level, "%s: Active connection %s, user %s, read %s (more than %s) characters since last check - prevent sleep.",
                            self.name, pid, username, read_since_last, self.max_read_chars)
                    else:
                        _LOG.log(level, "%s: connection %s assumed active, user %s - prevent sleep.", self.name, pid, username)

                    active_clients.append((pid, username))
                    continue

                if pid not in prev_clients :
                    _LOG.info("%s: Found connection %s, user '%s' - prevent sleep", self.name, pid, username)
                    active_clients.append((pid, username))
                    continue

                _LOG.log(
                    logging.INFO if prev_active else logging.DEBUG,
                    "%s: Inactive connection %s, user %s read %s (less than %s) characters since last check.",
                    self.name, pid, username, read_since_last, self.max_read_chars)

        for pid in prev_clients:
            if pid not in self.clients:
                _LOG.info("%s: Client %s has disconnected.", self.name, pid)

        if active_clients:
            return f"{len(active_clients)} active clients {active_clients}"

        if not self.clients:
            _LOG.log(logging.INFO if prev_clients else logging.DEBUG, "%s: No connections.", self.name)
            return ""

        _LOG.log(logging.INFO if prev_active_clients else logging.DEBUG, "%s: No active connections.", self.name)
        return ""

"""Check for (active) ssh clients."""

# Tested on Fedora 39
# Requires psutil

import logging

import psutil

from .checker import Checker


_LOG = logging.getLogger(__name__)


class SshChecker(Checker):
    """Check for *active* SSH clients."""
    def __init__(self, sleep_seconds: int, max_read_chars_per_second: int = 20):
        super().__init__(sleep_seconds=sleep_seconds)
        self.max_read_chars = max_read_chars_per_second * sleep_seconds
        self.clients: dict[int, tuple[int, bool, str]] = {}  # pid -> read_chars, active, username

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
                _LOG.debug("%s", info)
                pid = info["pid"]

                prev_read_chars, prev_active, _ = prev_clients.get(pid, (0, False, ""))
                prev_active_clients = prev_active_clients or prev_active

                try:
                    read_chars = info["io_counters"].read_chars
                    read_since_last = read_chars - prev_read_chars
                    active = read_since_last > self.max_read_chars
                except AttributeError as ex:
                    _LOG.warning("Must run as root to determine if SSH session is active. Assuming all sessions active. %s.", ex)
                    read_chars = 0
                    active = True

                self.clients[pid] = read_chars, active, username

                if active:
                    level = logging.INFO if not prev_active else logging.DEBUG
                    if read_chars:
                        _LOG.log(
                            level, "Active SSH connection %s, user %s, read %s (more than %s) characters since last check - prevent sleep.",
                            pid, username, read_since_last, self.max_read_chars)
                    else:
                        _LOG.log(level, "SSH connection %s assumed active, user %s - prevent sleep.", pid, username)

                    active_clients.append((pid, username))
                    continue

                if pid not in prev_clients :
                    _LOG.info("Found SSH connection %s, user '%s' - prevent sleep", pid, username)
                    active_clients.append((pid, username))
                    continue

                _LOG.log(
                    logging.INFO if prev_active else logging.DEBUG,
                    "Inactive SSH connection %s, user %s read %s (less than %s) characters since last check.",
                    pid, username, read_since_last, self.max_read_chars)

        for pid in prev_clients:
            if pid not in self.clients:
                _LOG.info("SSH client %s has disconnected.", pid)

        if active_clients:
            return f"{len(active_clients)} active clients {active_clients}"

        if not self.clients:
            _LOG.log(logging.INFO if prev_clients else logging.DEBUG, "No SSH connections")
            return ""

        _LOG.log(logging.INFO if prev_active_clients else logging.DEBUG, "No active SSH connections")
        return ""

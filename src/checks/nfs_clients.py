"""Check for (active) NFS clients."""

import os
from pathlib import Path
import logging

from .checker import Checker


_LOG = logging.getLogger(__name__)


class NfsChecker(Checker):
    """Check for NFS clients."""
    def __init__(self, sleep_seconds: int, clients_dir: Path = Path("/proc/fs/nfsd/clients")):
        super().__init__(sleep_seconds=sleep_seconds)
        self.clients_dir = clients_dir
        self.clients: set[tuple[str, str]] = set()
        self.client_dir_found = True  # Assumed

    def check(self) -> str:
        """Return non-empty str with info if any connected NFS clients are found.

        Most important info should be at start of return value, it may be truncated in D-Bus message.
        """

        if not self.clients_dir.exists():
            _LOG.log(
                logging.INFO if self.client_dir_found else logging.DEBUG,
                "No NFS clients - directory '%s' does not exist. ", self.clients_dir)
            self.client_dir_found = False
            return ""

        self.client_dir_found = True

        active_clients: list[tuple[str, str]] = []
        for client_dir in os.scandir(self.clients_dir):
            client_info = []
            with open(Path(client_dir)/"info", encoding="utf-8") as inf:
                for line in inf.readlines():
                    if line.startswith("name:") or line.startswith("address:"):
                        client_info.append(line.strip())

            key = (client_dir.name, ", ".join([line.split(":")[1].strip().strip('"') for line in client_info]))
            active_clients.append(key)
            _LOG.log(
                logging.INFO if key not in self.clients else logging.DEBUG,
                "Found NFS client %s - prevent sleep", client_info or client_dir)
            continue

        for client in self.clients:
            if client not in active_clients:
                _LOG.info("NFS client %s has disconnected.", client)

        if active_clients:
            self.clients = set(active_clients)
            return f"{len(active_clients)} clients {active_clients}"

        _LOG.log(logging.INFO if self.clients else logging.DEBUG, "No NFS clients.")
        self.clients = set(active_clients)
        return ""

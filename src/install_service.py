"""Install systemd service definition."""
import subprocess
from pathlib import Path
import logging

from . import __version__


_LOG = logging.getLogger(__name__)
_HERE = Path(__file__).parent
_SYSTEMD_DIR = Path("/etc/systemd/system")


def get_setuptools_entry_point_script() -> Path:
    """Figure out where setuptools installed the entry point script."""
    script_name = "prevent-sleep"
    parent_dir = _HERE
    while parent_dir != Path("/"):
        _LOG.debug("checking %s", parent_dir)
        script = parent_dir/"bin"/script_name
        if script.exists():
            out = subprocess.check_output([script, "--version"])
            if __version__ not in str(out):
                _LOG.warning("Found script %s, version %s, expected: %s", script, out, __version__)
                continue
            return script
        parent_dir = parent_dir.parent

    raise FileNotFoundError(script_name)


def install_service(systemd_dir: Path = _SYSTEMD_DIR):
    """Install the systemd service definition."""
    service_file_name = "prevent-sleep.service"
    src_file = Path(__file__).parent/"data"/service_file_name
    tgt_file = systemd_dir/service_file_name
    script = get_setuptools_entry_point_script()
    with open(src_file, encoding="utf-8") as srcf:
        with open(tgt_file, "w", encoding="utf-8") as tgtf:
            tgtf.write(srcf.read().replace("{{exectable_path}}", str(script)))

    _LOG.info("Service defintion installed to %s", tgt_file)
    _LOG.info("Execute: sudo systemctl enable --now prevent-sleep")
    _LOG.info("To enable and start service.")

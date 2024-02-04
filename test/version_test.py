import re

import prevent_sleep


def test_version_of_properly_installe_package():
    assert (re.match(r"[0-9]+\.[0-9]+\.[0-9]+.*", prevent_sleep.__version__) or
            re.match(r"0\.1\.dev.*", prevent_sleep.__version__))

import logging

import pytest

from prevent_sleep import prevent_sleep


@pytest.mark.parametrize("loglevel, loops", [(logging.INFO, 3), (logging.DEBUG, 2)])
def test_prevent_sleep(loglevel, loops):
    prevent_sleep.prevent_sleep(loglevel, check_interval_seconds=0.1, max_inactive_seconds=1, max_loops=loops)
    pytest.xfail("TODO")

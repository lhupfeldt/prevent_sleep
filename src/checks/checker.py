"""Checker interface."""

from abc import ABC, abstractmethod


class Checker(ABC):
    """Astract base class for checkers.

    Arguments:
        check_interval_seconds: The number of seconds between each call to `check`.
            Note that the check method must not sleep, the delay between intervals is handled outside of checkers.
    """

    def __init__(self, check_interval_seconds: int):
        self.check_interval_seconds = check_interval_seconds

    @property
    @abstractmethod
    def name(self) -> str:
        """A short name for this checker to be used in logging. E.g. 'SSH'"""
        raise NotImplementedError("name")

    @abstractmethod
    def check(self) -> str:
        """Execute one check and return result.

        Return:
            Must return non-empty str with info if sleep should be inhibited.
            Most important info should be at start of return value, it may be truncated in D-Bus messsage.
            The same string should be returned if the reason for wanting to sleep does not change.
            Must return an empty string if sleep should not be inhibited.
        """

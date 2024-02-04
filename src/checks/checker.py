"""Checker interface."""

from abc import ABC, abstractmethod


class Checker(ABC):
    """Astract base class for checkers."""
    def __init__(self, sleep_seconds: int):
        self.sleep_seconds = sleep_seconds

    @abstractmethod
    def check(self) -> str:
        """Must return non-empty str with info if sleep should be inhibited.

        Most important info should be at start of return value, it may be truncated in D-Bus messsage.
        The same string should be returned if the reason for wanting to sleep does not change.
        """

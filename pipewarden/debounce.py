"""Debounce notifications: only fire an alert after N consecutive failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class DebounceAlert:
    """Fired when a check has failed consecutively for *threshold* times."""

    check_name: str
    consecutive_failures: int
    last_result: CheckResult

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DebounceAlert(check={self.check_name!r}, "
            f"consecutive_failures={self.consecutive_failures})"
        )


class DebounceNotifier:
    """Wraps an alert handler and only calls it once the failure count
    reaches *threshold* consecutive failures for a given check.

    The counter resets as soon as a non-failing result is observed.
    """

    def __init__(
        self,
        threshold: int,
        handlers: List[Callable[[DebounceAlert], None]] | None = None,
    ) -> None:
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        self._threshold = threshold
        self._handlers: List[Callable[[DebounceAlert], None]] = list(handlers or [])
        self._counts: dict[str, int] = {}

    @property
    def threshold(self) -> int:
        return self._threshold

    def add_handler(self, handler: Callable[[DebounceAlert], None]) -> None:
        self._handlers.append(handler)

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def observe(self, result: CheckResult) -> bool:
        """Record *result* and fire handlers if the debounce threshold is met.

        Returns True if the alert was fired, False otherwise.
        """
        name = result.check_name
        if result.status in (CheckStatus.FAILED, CheckStatus.ERROR):
            self._counts[name] = self._counts.get(name, 0) + 1
        else:
            self._counts[name] = 0
            return False

        if self._counts[name] >= self._threshold:
            alert = DebounceAlert(
                check_name=name,
                consecutive_failures=self._counts[name],
                last_result=result,
            )
            for handler in self._handlers:
                handler(alert)
            return True
        return False

    def consecutive_failures(self, check_name: str) -> int:
        """Return the current consecutive-failure count for *check_name*."""
        return self._counts.get(check_name, 0)

    def reset(self, check_name: str) -> None:
        """Manually reset the counter for *check_name*."""
        self._counts.pop(check_name, None)

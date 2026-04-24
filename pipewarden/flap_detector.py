"""Flap detection for check results — identifies checks that oscillate between
passed and failed states within a sliding window."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import List

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class FlapAlert:
    """Emitted when a check is detected as flapping."""

    check_name: str
    transitions: int
    window_size: int

    def __repr__(self) -> str:
        return (
            f"FlapAlert(check={self.check_name!r}, "
            f"transitions={self.transitions}, window={self.window_size})"
        )


class FlapDetector:
    """Detects flapping behaviour for a single check.

    A check is considered flapping when the number of status transitions
    within the last *window_size* results meets or exceeds *threshold*.
    """

    def __init__(
        self,
        check_name: str,
        window_size: int = 10,
        threshold: int = 4,
    ) -> None:
        if window_size < 2:
            raise ValueError("window_size must be at least 2")
        if threshold < 1:
            raise ValueError("threshold must be at least 1")
        if threshold >= window_size:
            raise ValueError("threshold must be less than window_size")

        self._check_name = check_name
        self._window_size = window_size
        self._threshold = threshold
        self._window: deque[CheckStatus] = deque(maxlen=window_size)

    @property
    def check_name(self) -> str:
        return self._check_name

    @property
    def window_size(self) -> int:
        return self._window_size

    @property
    def threshold(self) -> int:
        return self._threshold

    def observe(self, result: CheckResult) -> FlapAlert | None:
        """Record a result and return a FlapAlert if flapping is detected."""
        if result.check_name != self._check_name:
            raise ValueError(
                f"Expected result for {self._check_name!r}, "
                f"got {result.check_name!r}"
            )
        self._window.append(result.status)
        transitions = self._count_transitions()
        if transitions >= self._threshold:
            return FlapAlert(
                check_name=self._check_name,
                transitions=transitions,
                window_size=len(self._window),
            )
        return None

    def transitions(self) -> int:
        """Return the current number of status transitions in the window."""
        return self._count_transitions()

    def reset(self) -> None:
        """Clear the observation window."""
        self._window.clear()

    def _count_transitions(self) -> int:
        statuses: List[CheckStatus] = list(self._window)
        return sum(
            1 for i in range(1, len(statuses)) if statuses[i] != statuses[i - 1]
        )

    def __repr__(self) -> str:
        return (
            f"FlapDetector(check={self._check_name!r}, "
            f"window={self._window_size}, threshold={self._threshold})"
        )

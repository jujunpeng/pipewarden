"""Sliding window aggregator for pipeline check results."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class WindowAggregator:
    """Aggregates CheckResults over a fixed-size sliding window per check."""

    check_name: str
    max_size: int = 20
    _window: Deque[CheckResult] = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_size < 1:
            raise ValueError("max_size must be at least 1")

    def record(self, result: CheckResult) -> None:
        if result.check_name != self.check_name:
            raise ValueError(
                f"Expected check_name '{self.check_name}', got '{result.check_name}'"
            )
        if len(self._window) >= self.max_size:
            self._window.popleft()
        self._window.append(result)

    @property
    def size(self) -> int:
        return len(self._window)

    @property
    def results(self) -> List[CheckResult]:
        return list(self._window)

    @property
    def pass_rate(self) -> float:
        if not self._window:
            return 0.0
        passed = sum(1 for r in self._window if r.status == CheckStatus.PASSED)
        return passed / len(self._window)

    @property
    def failure_streak(self) -> int:
        """Number of consecutive failures/errors at the end of the window."""
        streak = 0
        for result in reversed(self._window):
            if result.status != CheckStatus.PASSED:
                streak += 1
            else:
                break
        return streak

    @property
    def latest(self) -> Optional[CheckResult]:
        return self._window[-1] if self._window else None

    def reset(self) -> None:
        self._window.clear()

    def __repr__(self) -> str:
        return (
            f"WindowAggregator(check_name={self.check_name!r}, "
            f"max_size={self.max_size}, size={self.size}, "
            f"pass_rate={self.pass_rate:.2f})"
        )

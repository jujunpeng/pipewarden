"""Check budget: enforce a maximum allowed failure count over a time window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class BudgetViolation:
    check_name: str
    failures_observed: int
    budget: int
    window_seconds: float

    def __repr__(self) -> str:
        return (
            f"BudgetViolation(check={self.check_name!r}, "
            f"failures={self.failures_observed}/{self.budget}, "
            f"window={self.window_seconds}s)"
        )


@dataclass
class ErrorBudget:
    """Tracks failures for a single check within a rolling time window."""

    check_name: str
    max_failures: int
    window_seconds: float
    _history: List[datetime] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_failures < 0:
            raise ValueError("max_failures must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

    def observe(self, result: CheckResult) -> None:
        """Record a result; only failures are tracked."""
        if result.check_name != self.check_name:
            raise ValueError(
                f"Expected check {self.check_name!r}, got {result.check_name!r}"
            )
        now = result.timestamp
        self._evict(now)
        if result.status in (CheckStatus.FAILED, CheckStatus.ERROR):
            self._history.append(now)

    def _evict(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self.window_seconds)
        self._history = [ts for ts in self._history if ts > cutoff]

    @property
    def failure_count(self) -> int:
        return len(self._history)

    @property
    def remaining(self) -> int:
        return max(0, self.max_failures - self.failure_count)

    @property
    def exhausted(self) -> bool:
        return self.failure_count > self.max_failures

    def violation(self) -> BudgetViolation | None:
        if self.exhausted:
            return BudgetViolation(
                check_name=self.check_name,
                failures_observed=self.failure_count,
                budget=self.max_failures,
                window_seconds=self.window_seconds,
            )
        return None

    def reset(self) -> None:
        self._history.clear()

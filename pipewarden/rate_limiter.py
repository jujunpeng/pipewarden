"""Rate limiter for check execution — prevents a check from running more
frequently than a configured minimum interval."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class RateLimiter:
    """Enforces a minimum interval between executions of named checks."""

    min_interval_seconds: float
    _last_run: Dict[str, datetime] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.min_interval_seconds <= 0:
            raise ValueError(
                f"min_interval_seconds must be positive, got {self.min_interval_seconds}"
            )

    def is_allowed(self, check_name: str) -> bool:
        """Return True if the check may run now."""
        last = self._last_run.get(check_name)
        if last is None:
            return True
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        return elapsed >= self.min_interval_seconds

    def record(self, check_name: str) -> None:
        """Record that *check_name* ran right now."""
        self._last_run[check_name] = datetime.now(timezone.utc)

    def seconds_until_allowed(self, check_name: str) -> float:
        """Return seconds remaining before the check may run again (0 if allowed)."""
        last = self._last_run.get(check_name)
        if last is None:
            return 0.0
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        remaining = self.min_interval_seconds - elapsed
        return max(0.0, remaining)

    def reset(self, check_name: str) -> None:
        """Clear the recorded last-run time for *check_name*."""
        self._last_run.pop(check_name, None)

    def reset_all(self) -> None:
        """Clear all recorded last-run times."""
        self._last_run.clear()

    def last_run(self, check_name: str) -> Optional[datetime]:
        """Return the last recorded run time for *check_name*, or None if never run.

        The returned datetime is always timezone-aware (UTC).
        """
        return self._last_run.get(check_name)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RateLimiter(min_interval_seconds={self.min_interval_seconds}, "
            f"tracked={list(self._last_run.keys())})"
        )

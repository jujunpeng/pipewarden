"""Watchdog module for detecting stale or overdue health checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewarden.checks import CheckResult


@dataclass
class StalenessViolation:
    """Represents a check that has not run within its expected interval."""

    check_name: str
    last_seen: Optional[datetime]
    max_age_seconds: float
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        last = self.last_seen.isoformat() if self.last_seen else "never"
        return (
            f"StalenessViolation(check={self.check_name!r}, "
            f"last_seen={last}, max_age_seconds={self.max_age_seconds})"
        )


class CheckWatchdog:
    """Monitors check results and flags checks that have gone stale."""

    def __init__(self, max_age_seconds: float = 300.0) -> None:
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        self._max_age_seconds = max_age_seconds
        self._last_seen: Dict[str, datetime] = {}

    @property
    def max_age_seconds(self) -> float:
        return self._max_age_seconds

    def record(self, result: CheckResult) -> None:
        """Update the last-seen timestamp for a check."""
        self._last_seen[result.check_name] = result.timestamp

    def record_many(self, results: List[CheckResult]) -> None:
        """Update last-seen timestamps for multiple results."""
        for result in results:
            self.record(result)

    def violations(self, now: Optional[datetime] = None) -> List[StalenessViolation]:
        """Return a list of checks that have exceeded max_age_seconds."""
        now = now or datetime.utcnow()
        cutoff = timedelta(seconds=self._max_age_seconds)
        found: List[StalenessViolation] = []
        for name, last in self._last_seen.items():
            if now - last > cutoff:
                found.append(
                    StalenessViolation(
                        check_name=name,
                        last_seen=last,
                        max_age_seconds=self._max_age_seconds,
                        detected_at=now,
                    )
                )
        return found

    def is_stale(self, check_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if the named check is stale or has never been seen."""
        now = now or datetime.utcnow()
        if check_name not in self._last_seen:
            return True
        return (now - self._last_seen[check_name]).total_seconds() > self._max_age_seconds

    def known_checks(self) -> List[str]:
        """Return the names of all checks that have been recorded."""
        return list(self._last_seen.keys())

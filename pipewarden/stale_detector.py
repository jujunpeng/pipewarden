from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class StaleAlert:
    check_name: str
    last_seen: datetime
    age_seconds: float
    threshold_seconds: float

    def __repr__(self) -> str:
        return (
            f"StaleAlert(check={self.check_name!r}, "
            f"age={self.age_seconds:.1f}s, "
            f"threshold={self.threshold_seconds:.1f}s)"
        )


class StaleDetector:
    """Detects checks that have not reported a result within a threshold."""

    def __init__(self, default_threshold_seconds: float = 300.0) -> None:
        if default_threshold_seconds <= 0:
            raise ValueError("default_threshold_seconds must be positive")
        self._default_threshold = default_threshold_seconds
        self._last_seen: Dict[str, datetime] = {}
        self._overrides: Dict[str, float] = {}

    @property
    def default_threshold_seconds(self) -> float:
        return self._default_threshold

    def set_threshold(self, check_name: str, threshold_seconds: float) -> None:
        if threshold_seconds <= 0:
            raise ValueError("threshold_seconds must be positive")
        self._overrides[check_name] = threshold_seconds

    def observe(self, result: CheckResult) -> None:
        self._last_seen[result.check_name] = result.timestamp

    def check_stale(self, check_name: str, now: Optional[datetime] = None) -> Optional[StaleAlert]:
        if check_name not in self._last_seen:
            return None
        if now is None:
            now = datetime.now(timezone.utc)
        last = self._last_seen[check_name]
        age = (now - last).total_seconds()
        threshold = self._overrides.get(check_name, self._default_threshold)
        if age > threshold:
            return StaleAlert(
                check_name=check_name,
                last_seen=last,
                age_seconds=age,
                threshold_seconds=threshold,
            )
        return None

    def scan(self, now: Optional[datetime] = None) -> list[StaleAlert]:
        alerts = []
        for name in self._last_seen:
            alert = self.check_stale(name, now=now)
            if alert is not None:
                alerts.append(alert)
        return alerts

    def known_checks(self) -> list[str]:
        return list(self._last_seen.keys())

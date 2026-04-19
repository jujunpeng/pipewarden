"""Check duration profiling and slow-check detection."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class ProfileEntry:
    check_name: str
    duration_ms: float
    threshold_ms: float

    @property
    def is_slow(self) -> bool:
        return self.duration_ms > self.threshold_ms

    def __repr__(self) -> str:
        flag = "SLOW" if self.is_slow else "OK"
        return f"ProfileEntry({self.check_name!r}, {self.duration_ms:.1f}ms, [{flag}])"


class CheckProfiler:
    """Records check durations and flags slow checks against a threshold."""

    def __init__(self, threshold_ms: float = 1000.0) -> None:
        if threshold_ms <= 0:
            raise ValueError("threshold_ms must be positive")
        self._threshold_ms = threshold_ms
        self._entries: List[ProfileEntry] = []

    @property
    def threshold_ms(self) -> float:
        return self._threshold_ms

    def observe(self, result: CheckResult) -> ProfileEntry:
        if result.duration_ms is None:
            raise ValueError("CheckResult has no duration_ms")
        entry = ProfileEntry(
            check_name=result.check_name,
            duration_ms=result.duration_ms,
            threshold_ms=self._threshold_ms,
        )
        self._entries.append(entry)
        return entry

    def slow_checks(self) -> List[ProfileEntry]:
        return [e for e in self._entries if e.is_slow]

    def all_entries(self) -> List[ProfileEntry]:
        return list(self._entries)

    def reset(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

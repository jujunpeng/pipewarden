"""Check run quota enforcement — limits how many checks can run in a time window."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


@dataclass
class QuotaViolation:
    check_name: str
    limit: int
    window_seconds: float
    attempted_at: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return (
            f"QuotaViolation(check={self.check_name!r}, "
            f"limit={self.limit}, window={self.window_seconds}s)"
        )


class CheckQuota:
    """Sliding-window quota that allows at most *limit* runs per *window_seconds*."""

    def __init__(self, check_name: str, limit: int, window_seconds: float) -> None:
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._check_name = check_name
        self._limit = limit
        self._window_seconds = window_seconds
        self._timestamps: Deque[float] = deque()

    @property
    def check_name(self) -> str:
        return self._check_name

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def window_seconds(self) -> float:
        return self._window_seconds

    def _evict_old(self, now: float) -> None:
        cutoff = now - self._window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def is_allowed(self, now: float | None = None) -> bool:
        """Return True if another run is permitted right now."""
        now = now if now is not None else time.time()
        self._evict_old(now)
        return len(self._timestamps) < self._limit

    def record(self, now: float | None = None) -> None:
        """Record that a run occurred at *now*."""
        now = now if now is not None else time.time()
        self._evict_old(now)
        self._timestamps.append(now)

    def current_count(self, now: float | None = None) -> int:
        now = now if now is not None else time.time()
        self._evict_old(now)
        return len(self._timestamps)

    def violation(self, now: float | None = None) -> QuotaViolation:
        now = now if now is not None else time.time()
        return QuotaViolation(
            check_name=self._check_name,
            limit=self._limit,
            window_seconds=self._window_seconds,
            attempted_at=now,
        )

    def __repr__(self) -> str:
        return (
            f"CheckQuota(check={self._check_name!r}, "
            f"limit={self._limit}, window={self._window_seconds}s)"
        )

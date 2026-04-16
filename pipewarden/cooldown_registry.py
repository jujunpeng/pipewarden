"""Per-check cooldown tracking to suppress repeated alerts."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional


class CooldownRegistry:
    """Tracks last-alerted timestamps per check name to enforce cooldowns."""

    def __init__(self, default_cooldown_seconds: float = 300.0) -> None:
        if default_cooldown_seconds < 0:
            raise ValueError("default_cooldown_seconds must be non-negative")
        self._default_cooldown = default_cooldown_seconds
        self._last_alerted: Dict[str, datetime] = {}
        self._overrides: Dict[str, float] = {}

    @property
    def default_cooldown_seconds(self) -> float:
        return self._default_cooldown

    def set_override(self, check_name: str, cooldown_seconds: float) -> None:
        """Set a per-check cooldown override."""
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")
        self._overrides[check_name] = cooldown_seconds

    def remove_override(self, check_name: str) -> None:
        self._overrides.pop(check_name, None)

    def cooldown_for(self, check_name: str) -> float:
        return self._overrides.get(check_name, self._default_cooldown)

    def is_suppressed(self, check_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if the check is still within its cooldown window."""
        if check_name not in self._last_alerted:
            return False
        now = now or datetime.utcnow()
        elapsed = (now - self._last_alerted[check_name]).total_seconds()
        return elapsed < self.cooldown_for(check_name)

    def record(self, check_name: str, at: Optional[datetime] = None) -> None:
        """Record that an alert was sent for this check."""
        self._last_alerted[check_name] = at or datetime.utcnow()

    def reset(self, check_name: str) -> None:
        """Clear the cooldown record for a check."""
        self._last_alerted.pop(check_name, None)

    def reset_all(self) -> None:
        self._last_alerted.clear()

    def __len__(self) -> int:
        return len(self._last_alerted)

"""Deduplicator: suppress duplicate alerts for repeated identical check results."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class Deduplicator:
    """Tracks last-seen status per check and suppresses duplicate notifications."""

    _last_status: Dict[str, CheckStatus] = field(default_factory=dict, init=False)
    _suppressed_count: Dict[str, int] = field(default_factory=dict, init=False)

    def is_duplicate(self, result: CheckResult) -> bool:
        """Return True if the result status is identical to the last seen status."""
        name = result.check_name
        last = self._last_status.get(name)
        if last is not None and last == result.status:
            self._suppressed_count[name] = self._suppressed_count.get(name, 0) + 1
            return True
        self._last_status[name] = result.status
        return False

    def record(self, result: CheckResult) -> None:
        """Unconditionally update the last-seen status without duplicate logic."""
        self._last_status[result.check_name] = result.status

    def suppressed_count(self, check_name: str) -> int:
        """Return how many times alerts were suppressed for a given check."""
        return self._suppressed_count.get(check_name, 0)

    def reset(self, check_name: Optional[str] = None) -> None:
        """Reset state for one check or all checks if name is None."""
        if check_name is None:
            self._last_status.clear()
            self._suppressed_count.clear()
        else:
            self._last_status.pop(check_name, None)
            self._suppressed_count.pop(check_name, None)

    def known_checks(self) -> list[str]:
        """Return list of check names currently tracked."""
        return list(self._last_status.keys())

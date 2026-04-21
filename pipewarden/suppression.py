"""Check suppression rules — silence alerts for known/expected failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pipewarden.checks import CheckResult


@dataclass
class SuppressionRule:
    """Suppress alerts for a named check until a given expiry time."""

    check_name: str
    reason: str
    expires_at: Optional[datetime] = None  # None means suppress indefinitely

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if this rule is currently active."""
        if self.expires_at is None:
            return True
        now = now or datetime.now(timezone.utc)
        return now < self.expires_at

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SuppressionRule(check_name={self.check_name!r}, "
            f"reason={self.reason!r}, expires_at={self.expires_at!r})"
        )


class SuppressionRegistry:
    """Registry of active suppression rules."""

    def __init__(self) -> None:
        self._rules: dict[str, SuppressionRule] = {}

    def suppress(
        self,
        check_name: str,
        reason: str,
        expires_at: Optional[datetime] = None,
    ) -> SuppressionRule:
        """Add or replace a suppression rule for *check_name*."""
        if not check_name:
            raise ValueError("check_name must not be empty")
        if not reason:
            raise ValueError("reason must not be empty")
        if expires_at is not None and expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")
        rule = SuppressionRule(check_name=check_name, reason=reason, expires_at=expires_at)
        self._rules[check_name] = rule
        return rule

    def lift(self, check_name: str) -> None:
        """Remove suppression for *check_name* (no-op if not suppressed)."""
        self._rules.pop(check_name, None)

    def is_suppressed(self, check_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if *check_name* has an active suppression rule."""
        rule = self._rules.get(check_name)
        return rule is not None and rule.is_active(now)

    def filter(self, results: list[CheckResult], now: Optional[datetime] = None) -> list[CheckResult]:
        """Return only results whose checks are *not* suppressed."""
        return [r for r in results if not self.is_suppressed(r.check_name, now)]

    @property
    def active_rules(self) -> list[SuppressionRule]:
        """All currently active suppression rules."""
        now = datetime.now(timezone.utc)
        return [r for r in self._rules.values() if r.is_active(now)]

    def expire_stale(self) -> list[str]:
        """Remove all expired suppression rules and return their check names.

        Expired rules are those with a non-None ``expires_at`` that is in the
        past.  Indefinite rules (``expires_at=None``) are never removed.
        """
        now = datetime.now(timezone.utc)
        expired = [
            name for name, rule in self._rules.items()
            if rule.expires_at is not None and now >= rule.expires_at
        ]
        for name in expired:
            del self._rules[name]
        return expired

    def __len__(self) -> int:
        return len(self._rules)

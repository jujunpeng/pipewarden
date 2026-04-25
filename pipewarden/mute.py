"""Mute rules for suppressing alerts on specific checks during maintenance windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional

from pipewarden.checks import CheckResult


@dataclass
class MuteRule:
    """A rule that silences alerts for a check matching a predicate."""

    name: str
    condition: Callable[[CheckResult], bool]
    expires_at: Optional[datetime] = None

    def is_active(self) -> bool:
        """Return True if the rule has not expired."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at

    def matches(self, result: CheckResult) -> bool:
        """Return True if the rule is active and the condition matches."""
        if not self.is_active():
            return False
        try:
            return bool(self.condition(result))
        except Exception:
            return False

    def __repr__(self) -> str:
        expiry = self.expires_at.isoformat() if self.expires_at else "never"
        return f"MuteRule(name={self.name!r}, expires_at={expiry})"


class MuteRegistry:
    """Registry of mute rules; determines whether a result should be silenced."""

    def __init__(self) -> None:
        self._rules: List[MuteRule] = []

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def add(self, rule: MuteRule) -> None:
        if not isinstance(rule, MuteRule):
            raise TypeError("rule must be a MuteRule instance")
        self._rules.append(rule)

    def remove(self, name: str) -> None:
        self._rules = [r for r in self._rules if r.name != name]

    def is_muted(self, result: CheckResult) -> bool:
        """Return True if any active rule matches the result."""
        return any(r.matches(result) for r in self._rules)

    def purge_expired(self) -> int:
        """Remove expired rules and return the count removed."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.is_active()]
        return before - len(self._rules)

    def active_rules(self) -> List[MuteRule]:
        return [r for r in self._rules if r.is_active()]

    def __repr__(self) -> str:
        return f"MuteRegistry(rules={self.rule_count})"

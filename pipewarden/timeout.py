"""Timeout enforcement for health checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class TimeoutViolation:
    """Represents a check that exceeded its allowed duration."""

    check_name: str
    duration_ms: float
    limit_ms: float

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TimeoutViolation(check_name={self.check_name!r}, "
            f"duration_ms={self.duration_ms:.1f}, limit_ms={self.limit_ms:.1f})"
        )


@dataclass
class TimeoutPolicy:
    """Defines a per-check or global timeout limit in milliseconds."""

    limit_ms: float
    check_name: Optional[str] = None

    def __post_init__(self) -> None:
        if self.limit_ms <= 0:
            raise ValueError("limit_ms must be positive")

    def evaluate(self, result: CheckResult) -> Optional[TimeoutViolation]:
        """Return a TimeoutViolation if the result exceeded the limit, else None."""
        if result.duration_ms is None:
            return None
        if self.check_name is not None and result.check_name != self.check_name:
            return None
        if result.duration_ms > self.limit_ms:
            return TimeoutViolation(
                check_name=result.check_name,
                duration_ms=result.duration_ms,
                limit_ms=self.limit_ms,
            )
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TimeoutPolicy(limit_ms={self.limit_ms}, check_name={self.check_name!r})"
        )


class TimeoutMonitor:
    """Evaluates a collection of TimeoutPolicy objects against check results."""

    def __init__(self) -> None:
        self._policies: list[TimeoutPolicy] = []

    def add_policy(self, policy: TimeoutPolicy) -> None:
        if not isinstance(policy, TimeoutPolicy):
            raise TypeError("policy must be a TimeoutPolicy instance")
        self._policies.append(policy)

    @property
    def policy_count(self) -> int:
        return len(self._policies)

    def evaluate(self, result: CheckResult) -> list[TimeoutViolation]:
        """Return all violations triggered by the given result."""
        violations: list[TimeoutViolation] = []
        for policy in self._policies:
            violation = policy.evaluate(result)
            if violation is not None:
                violations.append(violation)
        return violations

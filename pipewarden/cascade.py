"""Cascade failure detection for pipewarden.

Detects when failures in one check trigger or correlate with failures
in downstream checks, helping identify root causes in ETL pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Sequence

from .checks import CheckResult, CheckStatus


@dataclass(frozen=True)
class CascadeAlert:
    """Emitted when a cascade failure pattern is detected."""

    root_check: str
    affected_checks: List[str]
    detected_at: datetime

    def __repr__(self) -> str:  # pragma: no cover
        affected = ", ".join(self.affected_checks)
        return (
            f"CascadeAlert(root={self.root_check!r}, "
            f"affected=[{affected}], detected_at={self.detected_at.isoformat()})"
        )


@dataclass
class CascadeRule:
    """Defines a directed dependency: if *upstream* fails, watch *downstream*.

    Args:
        name: Human-readable rule name.
        upstream: Name of the check considered the potential root cause.
        downstream: Names of checks expected to be affected by an upstream failure.
        condition: Optional callable that receives a ``CheckResult`` and returns
            ``True`` when the result counts as a failure for cascade purposes.
            Defaults to checking for FAILED or ERROR status.
    """

    name: str
    upstream: str
    downstream: List[str]
    condition: Optional[Callable[[CheckResult], bool]] = None

    def _is_failing(self, result: CheckResult) -> bool:
        if self.condition is not None:
            try:
                return bool(self.condition(result))
            except Exception:
                return False
        return result.status in (CheckStatus.FAILED, CheckStatus.ERROR)

    def evaluate(
        self, results: Sequence[CheckResult]
    ) -> Optional[CascadeAlert]:
        """Evaluate a batch of results against this rule.

        Returns a :class:`CascadeAlert` if the upstream check failed *and* at
        least one downstream check also failed; otherwise returns ``None``.

        Args:
            results: Collection of :class:`CheckResult` objects from a single
                pipeline run.
        """
        by_name: Dict[str, CheckResult] = {r.check_name: r for r in results}

        upstream_result = by_name.get(self.upstream)
        if upstream_result is None or not self._is_failing(upstream_result):
            return None

        affected = [
            name
            for name in self.downstream
            if name in by_name and self._is_failing(by_name[name])
        ]

        if not affected:
            return None

        return CascadeAlert(
            root_check=self.upstream,
            affected_checks=affected,
            detected_at=datetime.utcnow(),
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CascadeRule(name={self.name!r}, upstream={self.upstream!r}, "
            f"downstream={self.downstream!r})"
        )


class CascadeDetector:
    """Applies a set of :class:`CascadeRule` objects to pipeline results.

    Example::

        detector = CascadeDetector()
        detector.add_rule(CascadeRule(
            name="db-cascade",
            upstream="db_connection_check",
            downstream=["orders_check", "users_check"],
        ))
        alerts = detector.evaluate(results)

    """

    def __init__(self) -> None:
        self._rules: List[CascadeRule] = []

    @property
    def rule_count(self) -> int:
        """Number of registered cascade rules."""
        return len(self._rules)

    def add_rule(self, rule: CascadeRule) -> None:
        """Register a cascade rule.

        Args:
            rule: A :class:`CascadeRule` instance to add.

        Raises:
            TypeError: If *rule* is not a :class:`CascadeRule`.
        """
        if not isinstance(rule, CascadeRule):
            raise TypeError(f"Expected CascadeRule, got {type(rule).__name__}")
        self._rules.append(rule)

    def evaluate(self, results: Sequence[CheckResult]) -> List[CascadeAlert]:
        """Evaluate all registered rules against *results*.

        Args:
            results: Results from a single pipeline run.

        Returns:
            A list of :class:`CascadeAlert` objects, one per triggered rule.
        """
        alerts: List[CascadeAlert] = []
        for rule in self._rules:
            alert = rule.evaluate(results)
            if alert is not None:
                alerts.append(alert)
        return alerts

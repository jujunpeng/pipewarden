from __future__ import annotations
from typing import Dict, List, Optional
from pipewarden.checks import CheckResult
from pipewarden.dependency import DependencyGuard, DependencyViolation
from pipewarden.pipeline import PipelineReport


class DependencyAwareRunner:
    """
    Wraps a PipelineReport and a DependencyGuard to surface
    dependency violations alongside pipeline results.
    """

    def __init__(self, guard: DependencyGuard) -> None:
        if not isinstance(guard, DependencyGuard):
            raise TypeError("Expected a DependencyGuard instance.")
        self._guard = guard
        self._violations: List[DependencyViolation] = []

    @property
    def guard(self) -> DependencyGuard:
        return self._guard

    @property
    def last_violations(self) -> List[DependencyViolation]:
        return list(self._violations)

    def evaluate(self, report: PipelineReport) -> List[DependencyViolation]:
        if not isinstance(report, PipelineReport):
            raise TypeError("Expected a PipelineReport instance.")
        results: Dict[str, CheckResult] = {
            r.check_name: r for r in report.results
        }
        self._violations = self._guard.evaluate(results)
        return list(self._violations)

    def is_healthy(self, report: PipelineReport) -> bool:
        violations = self.evaluate(report)
        return report.passed and len(violations) == 0

    def __repr__(self) -> str:
        return (
            f"DependencyAwareRunner(rules={self._guard.rule_count}, "
            f"last_violations={len(self._violations)})"
        )

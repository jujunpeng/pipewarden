from __future__ import annotations
from typing import List
from pipewarden.dependency import DependencyGuard, DependencyViolation
from pipewarden.checks import CheckResult
from typing import Dict


class DependencyReport:
    def __init__(self, guard: DependencyGuard, results: Dict[str, CheckResult]) -> None:
        if not isinstance(guard, DependencyGuard):
            raise TypeError("Expected a DependencyGuard instance.")
        self._violations: List[DependencyViolation] = guard.evaluate(results)

    @property
    def violations(self) -> List[DependencyViolation]:
        return list(self._violations)

    @property
    def passed(self) -> bool:
        return len(self._violations) == 0

    def render(self) -> str:
        if self.passed:
            return "DependencyReport: all dependencies satisfied."
        lines = ["DependencyReport: violations detected:"]
        for v in self._violations:
            lines.append(f"  - {v.check_name} depends on {v.depends_on}: {v.reason}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"DependencyReport(violations={len(self._violations)})"

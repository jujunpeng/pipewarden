from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class DependencyViolation:
    check_name: str
    depends_on: str
    reason: str

    def __repr__(self) -> str:
        return (
            f"DependencyViolation(check={self.check_name!r}, "
            f"depends_on={self.depends_on!r}, reason={self.reason!r})"
        )


@dataclass
class DependencyRule:
    check_name: str
    depends_on: str
    condition: Callable[[CheckResult], bool] = field(default=lambda r: r.status == CheckStatus.PASSED)

    def evaluate(self, upstream: CheckResult) -> bool:
        try:
            return self.condition(upstream)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"DependencyRule(check={self.check_name!r}, depends_on={self.depends_on!r})"


class DependencyGuard:
    def __init__(self) -> None:
        self._rules: List[DependencyRule] = []

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def add_rule(self, rule: DependencyRule) -> None:
        if not isinstance(rule, DependencyRule):
            raise TypeError("Expected a DependencyRule instance.")
        self._rules.append(rule)

    def evaluate(self, results: Dict[str, CheckResult]) -> List[DependencyViolation]:
        violations: List[DependencyViolation] = []
        for rule in self._rules:
            upstream = results.get(rule.depends_on)
            if upstream is None:
                violations.append(
                    DependencyViolation(
                        check_name=rule.check_name,
                        depends_on=rule.depends_on,
                        reason=f"upstream check '{rule.depends_on}' not found in results",
                    )
                )
            elif not rule.evaluate(upstream):
                violations.append(
                    DependencyViolation(
                        check_name=rule.check_name,
                        depends_on=rule.depends_on,
                        reason=f"upstream check '{rule.depends_on}' did not satisfy condition",
                    )
                )
        return violations

    def clear(self) -> None:
        self._rules.clear()

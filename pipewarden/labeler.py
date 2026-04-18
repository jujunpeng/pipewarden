"""Assigns severity labels to check results based on configurable rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from pipewarden.checks import CheckResult, CheckStatus


Severity = str

PASS = "pass"
WARN = "warn"
CRITICAL = "critical"
UNKNOWN = "unknown"


@dataclass
class LabelRule:
    severity: Severity
    condition: Callable[[CheckResult], bool]
    description: str = ""

    def matches(self, result: CheckResult) -> bool:
        try:
            return self.condition(result)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"LabelRule(severity={self.severity!r}, description={self.description!r})"


class ResultLabeler:
    """Evaluates an ordered list of LabelRules against a CheckResult.

    Rules are evaluated in insertion order; the first match wins.
    Falls back to a default severity when no rule matches.
    """

    def __init__(self, default_severity: Severity = UNKNOWN) -> None:
        if not isinstance(default_severity, str) or not default_severity:
            raise ValueError("default_severity must be a non-empty string")
        self._default = default_severity
        self._rules: List[LabelRule] = []

    @property
    def default_severity(self) -> Severity:
        return self._default

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def add_rule(self, rule: LabelRule) -> None:
        if not isinstance(rule, LabelRule):
            raise TypeError("Expected a LabelRule instance")
        self._rules.append(rule)

    def label(self, result: CheckResult) -> Severity:
        for rule in self._rules:
            if rule.matches(result):
                return rule.severity
        return self._default

    def label_all(self, results: List[CheckResult]) -> dict[str, Severity]:
        return {r.check_name: self.label(r) for r in results}

    def clear(self) -> None:
        self._rules.clear()

    def __repr__(self) -> str:
        return (
            f"ResultLabeler(default_severity={self._default!r}, "
            f"rules={self.rule_count})"
        )

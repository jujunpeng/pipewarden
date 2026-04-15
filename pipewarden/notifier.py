"""Notification routing for pipeline check results."""

from __future__ import annotations

from typing import Callable, List, Optional

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.pipeline import PipelineReport


NotifyFn = Callable[[PipelineReport], None]


class NotificationRule:
    """Associates a condition with a notification callback."""

    def __init__(self, condition: Callable[[PipelineReport], bool], callback: NotifyFn, name: str = "") -> None:
        self.condition = condition
        self.callback = callback
        self.name = name or callback.__name__

    def matches(self, report: PipelineReport) -> bool:
        try:
            return bool(self.condition(report))
        except Exception:
            return False


class PipelineNotifier:
    """Routes a PipelineReport to registered notification rules."""

    def __init__(self) -> None:
        self._rules: List[NotificationRule] = []

    def add_rule(self, condition: Callable[[PipelineReport], bool], callback: NotifyFn, name: str = "") -> None:
        """Register a new notification rule."""
        self._rules.append(NotificationRule(condition, callback, name))

    def on_any_failure(self, callback: NotifyFn) -> None:
        """Convenience: notify when any check fails."""
        self.add_rule(lambda r: not r.passed(), callback, name="on_any_failure")

    def on_all_passed(self, callback: NotifyFn) -> None:
        """Convenience: notify when all checks pass."""
        self.add_rule(lambda r: r.passed(), callback, name="on_all_passed")

    def notify(self, report: PipelineReport) -> List[str]:
        """Evaluate rules and invoke matching callbacks. Returns names of triggered rules."""
        triggered: List[str] = []
        for rule in self._rules:
            if rule.matches(report):
                rule.callback(report)
                triggered.append(rule.name)
        return triggered

    @property
    def rule_count(self) -> int:
        return len(self._rules)

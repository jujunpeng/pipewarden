"""Tests for pipewarden.notifier."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.notifier import NotificationRule, PipelineNotifier
from pipewarden.pipeline import PipelineReport, PipelineCheck


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="", duration_ms=1.0)


def _make_report(statuses: list[CheckStatus]) -> PipelineReport:
    checks = [
        PipelineCheck(name=f"check_{i}", result=_make_result(f"check_{i}", s))
        for i, s in enumerate(statuses)
    ]
    return PipelineReport(checks=checks)


class TestNotificationRule:
    def test_matches_returns_true_when_condition_true(self):
        rule = NotificationRule(condition=lambda r: True, callback=lambda r: None, name="always")
        report = _make_report([CheckStatus.PASSED])
        assert rule.matches(report) is True

    def test_matches_returns_false_when_condition_false(self):
        rule = NotificationRule(condition=lambda r: False, callback=lambda r: None, name="never")
        report = _make_report([CheckStatus.PASSED])
        assert rule.matches(report) is False

    def test_matches_returns_false_on_exception(self):
        def bad_condition(r):
            raise RuntimeError("boom")

        rule = NotificationRule(condition=bad_condition, callback=lambda r: None)
        report = _make_report([CheckStatus.PASSED])
        assert rule.matches(report) is False

    def test_name_defaults_to_callback_name(self):
        def my_callback(r):
            pass

        rule = NotificationRule(condition=lambda r: True, callback=my_callback)
        assert rule.name == "my_callback"


class TestPipelineNotifier:
    def setup_method(self):
        self.notifier = PipelineNotifier()

    def test_initial_rule_count_is_zero(self):
        assert self.notifier.rule_count == 0

    def test_add_rule_increments_count(self):
        self.notifier.add_rule(lambda r: True, lambda r: None, name="test")
        assert self.notifier.rule_count == 1

    def test_notify_triggers_matching_rules(self):
        cb = MagicMock()
        self.notifier.add_rule(lambda r: True, cb, name="always")
        report = _make_report([CheckStatus.PASSED])
        triggered = self.notifier.notify(report)
        cb.assert_called_once_with(report)
        assert "always" in triggered

    def test_notify_skips_non_matching_rules(self):
        cb = MagicMock()
        self.notifier.add_rule(lambda r: False, cb, name="never")
        report = _make_report([CheckStatus.PASSED])
        triggered = self.notifier.notify(report)
        cb.assert_not_called()
        assert triggered == []

    def test_on_any_failure_triggers_on_failed_report(self):
        cb = MagicMock()
        self.notifier.on_any_failure(cb)
        report = _make_report([CheckStatus.PASSED, CheckStatus.FAILED])
        self.notifier.notify(report)
        cb.assert_called_once()

    def test_on_any_failure_silent_on_all_passed(self):
        cb = MagicMock()
        self.notifier.on_any_failure(cb)
        report = _make_report([CheckStatus.PASSED, CheckStatus.PASSED])
        self.notifier.notify(report)
        cb.assert_not_called()

    def test_on_all_passed_triggers_when_all_pass(self):
        cb = MagicMock()
        self.notifier.on_all_passed(cb)
        report = _make_report([CheckStatus.PASSED])
        self.notifier.notify(report)
        cb.assert_called_once()

    def test_notify_returns_list_of_triggered_rule_names(self):
        self.notifier.add_rule(lambda r: True, lambda r: None, name="rule_a")
        self.notifier.add_rule(lambda r: False, lambda r: None, name="rule_b")
        self.notifier.add_rule(lambda r: True, lambda r: None, name="rule_c")
        report = _make_report([CheckStatus.PASSED])
        triggered = self.notifier.notify(report)
        assert triggered == ["rule_a", "rule_c"]

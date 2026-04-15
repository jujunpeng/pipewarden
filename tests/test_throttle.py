"""Tests for pipewarden.throttle."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.notifier import PipelineNotifier
from pipewarden.pipeline import PipelineReport, PipelineCheck
from pipewarden.throttle import ThrottledNotifier


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="", duration_ms=1.0)


def _make_report(statuses: list[CheckStatus]) -> PipelineReport:
    checks = [
        PipelineCheck(name=f"c_{i}", result=_make_result(f"c_{i}", s))
        for i, s in enumerate(statuses)
    ]
    return PipelineReport(checks=checks)


class TestThrottledNotifier:
    def setup_method(self):
        self.inner = PipelineNotifier()
        self.throttled = ThrottledNotifier(self.inner, cooldown_seconds=10.0)
        self.report = _make_report([CheckStatus.FAILED])

    def test_raises_on_negative_cooldown(self):
        with pytest.raises(ValueError):
            ThrottledNotifier(self.inner, cooldown_seconds=-1)

    def test_cooldown_seconds_property(self):
        assert self.throttled.cooldown_seconds == 10.0

    def test_first_notify_triggers_callback(self):
        cb = MagicMock()
        self.inner.add_rule(lambda r: True, cb, name="rule1")
        triggered = self.throttled.notify(self.report)
        cb.assert_called_once()
        assert "rule1" in triggered

    def test_second_notify_suppressed_within_cooldown(self):
        cb = MagicMock()
        self.inner.add_rule(lambda r: True, cb, name="rule1")
        self.throttled.notify(self.report)
        triggered = self.throttled.notify(self.report)
        assert cb.call_count == 1
        assert triggered == []

    def test_notify_fires_again_after_cooldown(self):
        cb = MagicMock()
        self.inner.add_rule(lambda r: True, cb, name="rule1")

        base = 1000.0
        with patch("pipewarden.throttle.time.monotonic", side_effect=[base, base + 11.0, base + 11.0]):
            self.throttled.notify(self.report)
            triggered = self.throttled.notify(self.report)

        assert cb.call_count == 2
        assert "rule1" in triggered

    def test_is_throttled_false_before_first_notify(self):
        self.inner.add_rule(lambda r: True, lambda r: None, name="rule1")
        assert self.throttled.is_throttled("rule1") is False

    def test_is_throttled_true_after_notify(self):
        cb = MagicMock()
        self.inner.add_rule(lambda r: True, cb, name="rule1")
        self.throttled.notify(self.report)
        assert self.throttled.is_throttled("rule1") is True

    def test_reset_specific_rule_clears_throttle(self):
        cb = MagicMock()
        self.inner.add_rule(lambda r: True, cb, name="rule1")
        self.throttled.notify(self.report)
        self.throttled.reset("rule1")
        assert self.throttled.is_throttled("rule1") is False

    def test_reset_all_clears_all_throttles(self):
        for name in ("r1", "r2"):
            self.inner.add_rule(lambda r: True, lambda r: None, name=name)
        self.throttled.notify(self.report)
        self.throttled.reset()
        assert self.throttled.is_throttled("r1") is False
        assert self.throttled.is_throttled("r2") is False

    def test_zero_cooldown_never_throttles(self):
        throttled = ThrottledNotifier(self.inner, cooldown_seconds=0.0)
        cb = MagicMock()
        self.inner.add_rule(lambda r: True, cb, name="rule_z")
        throttled.notify(self.report)
        throttled.notify(self.report)
        assert cb.call_count == 2

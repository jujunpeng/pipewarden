"""Tests for pipewarden.suppression."""
from datetime import datetime, timedelta, timezone

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.suppression import SuppressionRegistry, SuppressionRule


def _make_result(name: str, status: CheckStatus = CheckStatus.FAILED) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="msg")


class TestSuppressionRule:
    def test_active_when_no_expiry(self):
        rule = SuppressionRule(check_name="c", reason="r")
        assert rule.is_active() is True

    def test_active_before_expiry(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        rule = SuppressionRule(check_name="c", reason="r", expires_at=future)
        assert rule.is_active() is True

    def test_inactive_after_expiry(self):
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        rule = SuppressionRule(check_name="c", reason="r", expires_at=past)
        assert rule.is_active() is False

    def test_is_active_uses_provided_now(self):
        expiry = datetime(2030, 1, 1, tzinfo=timezone.utc)
        rule = SuppressionRule(check_name="c", reason="r", expires_at=expiry)
        before = datetime(2029, 12, 31, tzinfo=timezone.utc)
        after = datetime(2030, 1, 2, tzinfo=timezone.utc)
        assert rule.is_active(now=before) is True
        assert rule.is_active(now=after) is False


class TestSuppressionRegistry:
    def setup_method(self):
        self.reg = SuppressionRegistry()

    def test_initial_len_zero(self):
        assert len(self.reg) == 0

    def test_suppress_adds_rule(self):
        self.reg.suppress("check_a", "planned maintenance")
        assert len(self.reg) == 1

    def test_is_suppressed_true_after_suppress(self):
        self.reg.suppress("check_a", "reason")
        assert self.reg.is_suppressed("check_a") is True

    def test_is_suppressed_false_for_unknown(self):
        assert self.reg.is_suppressed("unknown") is False

    def test_lift_removes_rule(self):
        self.reg.suppress("check_a", "reason")
        self.reg.lift("check_a")
        assert self.reg.is_suppressed("check_a") is False

    def test_lift_unknown_is_noop(self):
        self.reg.lift("nonexistent")  # should not raise

    def test_suppress_replaces_existing(self):
        self.reg.suppress("check_a", "first")
        self.reg.suppress("check_a", "second")
        assert len(self.reg) == 1
        assert self.reg._rules["check_a"].reason == "second"

    def test_raises_on_empty_check_name(self):
        with pytest.raises(ValueError, match="check_name"):
            self.reg.suppress("", "reason")

    def test_raises_on_empty_reason(self):
        with pytest.raises(ValueError, match="reason"):
            self.reg.suppress("check_a", "")

    def test_filter_removes_suppressed(self):
        self.reg.suppress("check_a", "reason")
        results = [_make_result("check_a"), _make_result("check_b")]
        filtered = self.reg.filter(results)
        assert len(filtered) == 1
        assert filtered[0].check_name == "check_b"

    def test_filter_returns_all_when_none_suppressed(self):
        results = [_make_result("check_a"), _make_result("check_b")]
        assert len(self.reg.filter(results)) == 2

    def test_active_rules_excludes_expired(self):
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.reg.suppress("check_a", "active")
        self.reg.suppress("check_b", "expired", expires_at=past)
        active = self.reg.active_rules
        names = [r.check_name for r in active]
        assert "check_a" in names
        assert "check_b" not in names

    def test_is_suppressed_false_after_expiry(self):
        past = datetime.now(timezone.utc) - timedelta(seconds=5)
        self.reg.suppress("check_a", "reason", expires_at=past)
        assert self.reg.is_suppressed("check_a") is False

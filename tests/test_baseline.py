"""Tests for pipewarden.baseline."""

import pytest

from pipewarden.baseline import BaselineMonitor, BaselineStats, BaselineViolation
from pipewarden.checks import CheckResult, CheckStatus


def _make_result(
    name: str = "my_check",
    status: CheckStatus = CheckStatus.PASSED,
    duration_ms: float = 50.0,
    message: str = "",
) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message=message,
        duration_ms=duration_ms,
    )


class TestBaselineStats:
    def test_valid_construction(self):
        stats = BaselineStats("check", expected_pass_rate=0.9, expected_max_duration_ms=200.0)
        assert stats.check_name == "check"
        assert stats.expected_pass_rate == 0.9
        assert stats.expected_max_duration_ms == 200.0

    def test_default_no_duration(self):
        stats = BaselineStats("check", expected_pass_rate=1.0)
        assert stats.expected_max_duration_ms is None

    def test_raises_on_pass_rate_above_one(self):
        with pytest.raises(ValueError, match="expected_pass_rate"):
            BaselineStats("check", expected_pass_rate=1.1)

    def test_raises_on_negative_pass_rate(self):
        with pytest.raises(ValueError, match="expected_pass_rate"):
            BaselineStats("check", expected_pass_rate=-0.1)

    def test_raises_on_zero_duration(self):
        with pytest.raises(ValueError, match="expected_max_duration_ms"):
            BaselineStats("check", expected_pass_rate=0.8, expected_max_duration_ms=0)

    def test_raises_on_negative_duration(self):
        with pytest.raises(ValueError, match="expected_max_duration_ms"):
            BaselineStats("check", expected_pass_rate=0.8, expected_max_duration_ms=-10.0)


class TestBaselineMonitor:
    def setup_method(self):
        self.monitor = BaselineMonitor()

    def test_get_returns_none_when_unregistered(self):
        assert self.monitor.get("unknown") is None

    def test_register_and_get(self):
        stats = BaselineStats("check_a", expected_pass_rate=0.95)
        self.monitor.register(stats)
        assert self.monitor.get("check_a") is stats

    def test_register_replaces_existing(self):
        s1 = BaselineStats("check_a", expected_pass_rate=0.9)
        s2 = BaselineStats("check_a", expected_pass_rate=0.8)
        self.monitor.register(s1)
        self.monitor.register(s2)
        assert self.monitor.get("check_a").expected_pass_rate == 0.8

    def test_evaluate_no_baseline_returns_none(self):
        result = _make_result(name="orphan")
        assert self.monitor.evaluate(result) is None

    def test_evaluate_passed_within_duration_returns_none(self):
        self.monitor.register(BaselineStats("c", expected_pass_rate=1.0, expected_max_duration_ms=100.0))
        result = _make_result(name="c", status=CheckStatus.PASSED, duration_ms=80.0)
        assert self.monitor.evaluate(result) is None

    def test_evaluate_duration_exceeded_returns_violation(self):
        self.monitor.register(BaselineStats("c", expected_pass_rate=1.0, expected_max_duration_ms=100.0))
        result = _make_result(name="c", status=CheckStatus.PASSED, duration_ms=150.0)
        violation = self.monitor.evaluate(result)
        assert isinstance(violation, BaselineViolation)
        assert "duration" in violation.reason
        assert violation.check_name == "c"

    def test_evaluate_failed_status_returns_violation(self):
        self.monitor.register(BaselineStats("c", expected_pass_rate=1.0))
        result = _make_result(name="c", status=CheckStatus.FAILED)
        violation = self.monitor.evaluate(result)
        assert isinstance(violation, BaselineViolation)
        assert "pass rate" in violation.reason

    def test_evaluate_error_status_returns_violation(self):
        self.monitor.register(BaselineStats("c", expected_pass_rate=0.5))
        result = _make_result(name="c", status=CheckStatus.ERROR)
        violation = self.monitor.evaluate(result)
        assert isinstance(violation, BaselineViolation)

    def test_evaluate_duration_none_skips_duration_check(self):
        self.monitor.register(BaselineStats("c", expected_pass_rate=1.0, expected_max_duration_ms=10.0))
        result = CheckResult(check_name="c", status=CheckStatus.PASSED, message="", duration_ms=None)
        assert self.monitor.evaluate(result) is None

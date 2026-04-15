"""Tests for pipewarden.metrics."""

from __future__ import annotations

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.metrics import CheckMetrics, MetricsCollector


def _make_result(
    name: str = "my_check",
    status: CheckStatus = CheckStatus.PASSED,
    duration_ms: float | None = 10.0,
) -> CheckResult:
    return CheckResult(check_name=name, status=status, duration_ms=duration_ms)


class TestCheckMetrics:
    def test_initial_values(self):
        m = CheckMetrics(name="c")
        assert m.total_runs == 0
        assert m.passed_runs == 0
        assert m.failed_runs == 0
        assert m.error_runs == 0
        assert m.durations_ms == []

    def test_pass_rate_zero_when_no_runs(self):
        m = CheckMetrics(name="c")
        assert m.pass_rate == 0.0

    def test_pass_rate_calculation(self):
        m = CheckMetrics(name="c", total_runs=4, passed_runs=3)
        assert m.pass_rate == pytest.approx(0.75)

    def test_avg_duration_ms_zero_when_empty(self):
        m = CheckMetrics(name="c")
        assert m.avg_duration_ms == 0.0

    def test_avg_duration_ms_calculation(self):
        m = CheckMetrics(name="c", durations_ms=[10.0, 20.0, 30.0])
        assert m.avg_duration_ms == pytest.approx(20.0)


class TestMetricsCollector:
    def setup_method(self):
        self.collector = MetricsCollector()

    def test_record_passed(self):
        self.collector.record(_make_result(status=CheckStatus.PASSED))
        m = self.collector.get("my_check")
        assert m.total_runs == 1
        assert m.passed_runs == 1
        assert m.failed_runs == 0
        assert m.error_runs == 0

    def test_record_failed(self):
        self.collector.record(_make_result(status=CheckStatus.FAILED))
        m = self.collector.get("my_check")
        assert m.failed_runs == 1

    def test_record_error(self):
        self.collector.record(_make_result(status=CheckStatus.ERROR))
        m = self.collector.get("my_check")
        assert m.error_runs == 1

    def test_duration_recorded(self):
        self.collector.record(_make_result(duration_ms=42.5))
        m = self.collector.get("my_check")
        assert m.durations_ms == [42.5]

    def test_duration_none_not_recorded(self):
        self.collector.record(_make_result(duration_ms=None))
        m = self.collector.get("my_check")
        assert m.durations_ms == []

    def test_multiple_records_accumulate(self):
        for _ in range(3):
            self.collector.record(_make_result(status=CheckStatus.PASSED))
        self.collector.record(_make_result(status=CheckStatus.FAILED))
        m = self.collector.get("my_check")
        assert m.total_runs == 4
        assert m.passed_runs == 3
        assert m.failed_runs == 1
        assert m.pass_rate == pytest.approx(0.75)

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError, match="unknown"):
            self.collector.get("unknown")

    def test_all_metrics_returns_all(self):
        self.collector.record(_make_result(name="a"))
        self.collector.record(_make_result(name="b"))
        all_m = self.collector.all_metrics()
        assert set(all_m.keys()) == {"a", "b"}

    def test_reset_clears_metrics(self):
        self.collector.record(_make_result())
        self.collector.reset()
        assert self.collector.all_metrics() == {}

    def test_separate_checks_tracked_independently(self):
        self.collector.record(_make_result(name="x", status=CheckStatus.PASSED))
        self.collector.record(_make_result(name="y", status=CheckStatus.FAILED))
        assert self.collector.get("x").passed_runs == 1
        assert self.collector.get("y").failed_runs == 1

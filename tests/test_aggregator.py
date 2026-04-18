"""Tests for pipewarden.aggregator."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.aggregator import ResultAggregator, AggregatedSummary


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="msg")


class TestResultAggregator:
    def setup_method(self):
        self.agg = ResultAggregator()

    def test_initial_check_names_empty(self):
        assert self.agg.check_names() == []

    def test_record_adds_check_name(self):
        self.agg.record(_make_result("c1", CheckStatus.PASSED))
        assert "c1" in self.agg.check_names()

    def test_summary_zero_runs_before_record(self):
        s = self.agg.summary("missing")
        assert s.total_runs == 0
        assert s.pass_rate == 0.0

    def test_pass_rate_all_passed(self):
        for _ in range(4):
            self.agg.record(_make_result("c1", CheckStatus.PASSED))
        s = self.agg.summary("c1")
        assert s.pass_rate == 1.0
        assert s.pass_count == 4

    def test_pass_rate_mixed(self):
        self.agg.record(_make_result("c1", CheckStatus.PASSED))
        self.agg.record(_make_result("c1", CheckStatus.FAILED))
        self.agg.record(_make_result("c1", CheckStatus.FAILED))
        s = self.agg.summary("c1")
        assert s.total_runs == 3
        assert s.pass_count == 1
        assert s.fail_count == 2
        assert pytest.approx(s.pass_rate) == 1 / 3

    def test_error_count(self):
        self.agg.record(_make_result("c2", CheckStatus.ERROR))
        self.agg.record(_make_result("c2", CheckStatus.ERROR))
        s = self.agg.summary("c2")
        assert s.error_count == 2
        assert s.pass_count == 0

    def test_record_many(self):
        results = [_make_result("c3", CheckStatus.PASSED) for _ in range(5)]
        self.agg.record_many(results)
        assert self.agg.summary("c3").total_runs == 5

    def test_all_summaries_returns_one_per_check(self):
        self.agg.record(_make_result("a", CheckStatus.PASSED))
        self.agg.record(_make_result("b", CheckStatus.FAILED))
        summaries = self.agg.all_summaries()
        names = {s.check_name for s in summaries}
        assert names == {"a", "b"}

    def test_reset_clears_data(self):
        self.agg.record(_make_result("c1", CheckStatus.PASSED))
        self.agg.reset()
        assert self.agg.check_names() == []

    def test_repr(self):
        self.agg.record(_make_result("c1", CheckStatus.PASSED))
        s = self.agg.summary("c1")
        assert "c1" in repr(s)
        assert "pass_rate" in repr(s)

"""Tests for WindowAggregator and WindowRegistry."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.window_aggregator import WindowAggregator
from pipewarden.window_registry import WindowRegistry


def _make_result(name: str, status: CheckStatus, duration: float = 0.1) -> CheckResult:
    return CheckResult(check_name=name, status=status, duration_ms=duration)


class TestWindowAggregator:
    def setup_method(self):
        self.agg = WindowAggregator(check_name="db.ping", max_size=3)

    def test_raises_on_zero_max_size(self):
        with pytest.raises(ValueError):
            WindowAggregator(check_name="x", max_size=0)

    def test_raises_on_wrong_check_name(self):
        r = _make_result("other", CheckStatus.PASSED)
        with pytest.raises(ValueError):
            self.agg.record(r)

    def test_initial_size_is_zero(self):
        assert self.agg.size == 0

    def test_record_increments_size(self):
        self.agg.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.agg.size == 1

    def test_window_evicts_oldest_when_full(self):
        for _ in range(4):
            self.agg.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.agg.size == 3

    def test_pass_rate_all_passed(self):
        for _ in range(3):
            self.agg.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.agg.pass_rate == 1.0

    def test_pass_rate_zero_when_empty(self):
        assert self.agg.pass_rate == 0.0

    def test_pass_rate_mixed(self):
        self.agg.record(_make_result("db.ping", CheckStatus.PASSED))
        self.agg.record(_make_result("db.ping", CheckStatus.FAILED))
        assert self.agg.pass_rate == pytest.approx(0.5)

    def test_failure_streak_zero_when_last_passed(self):
        self.agg.record(_make_result("db.ping", CheckStatus.FAILED))
        self.agg.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.agg.failure_streak == 0

    def test_failure_streak_counts_trailing_failures(self):
        self.agg.record(_make_result("db.ping", CheckStatus.PASSED))
        self.agg.record(_make_result("db.ping", CheckStatus.FAILED))
        self.agg.record(_make_result("db.ping", CheckStatus.FAILED))
        assert self.agg.failure_streak == 2

    def test_latest_returns_last_recorded(self):
        r = _make_result("db.ping", CheckStatus.FAILED)
        self.agg.record(_make_result("db.ping", CheckStatus.PASSED))
        self.agg.record(r)
        assert self.agg.latest is r

    def test_latest_none_when_empty(self):
        assert self.agg.latest is None

    def test_reset_clears_window(self):
        self.agg.record(_make_result("db.ping", CheckStatus.PASSED))
        self.agg.reset()
        assert self.agg.size == 0

    def test_repr_contains_check_name(self):
        assert "db.ping" in repr(self.agg)


class TestWindowRegistry:
    def setup_method(self):
        self.reg = WindowRegistry(default_max_size=5)

    def test_raises_on_zero_default_max_size(self):
        with pytest.raises(ValueError):
            WindowRegistry(default_max_size=0)

    def test_initial_len_is_zero(self):
        assert len(self.reg) == 0

    def test_record_creates_aggregator(self):
        self.reg.record(_make_result("svc.health", CheckStatus.PASSED))
        assert len(self.reg) == 1

    def test_get_returns_aggregator(self):
        self.reg.record(_make_result("svc.health", CheckStatus.PASSED))
        agg = self.reg.get("svc.health")
        assert agg.check_name == "svc.health"

    def test_get_raises_for_unknown_check(self):
        with pytest.raises(KeyError):
            self.reg.get("unknown")

    def test_check_names_lists_all(self):
        self.reg.record(_make_result("a", CheckStatus.PASSED))
        self.reg.record(_make_result("b", CheckStatus.FAILED))
        assert set(self.reg.check_names()) == {"a", "b"}

    def test_repr_contains_default_max_size(self):
        assert "5" in repr(self.reg)

import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.trend import TrendWindow, TrendTracker
from datetime import datetime


def _make_result(name: str, status: CheckStatus, duration: float = 1.0) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="ok",
        duration_ms=duration,
        timestamp=datetime.utcnow(),
    )


class TestTrendWindow:
    def setup_method(self):
        self.window = TrendWindow(check_name="db.ping", max_size=5)

    def test_raises_on_zero_max_size(self):
        with pytest.raises(ValueError):
            TrendWindow("x", max_size=0)

    def test_raises_on_wrong_check_name(self):
        result = _make_result("other", CheckStatus.PASSED)
        with pytest.raises(ValueError):
            self.window.record(result)

    def test_initial_size_is_zero(self):
        assert self.window.size == 0

    def test_record_increments_size(self):
        self.window.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.window.size == 1

    def test_max_size_enforced(self):
        for _ in range(7):
            self.window.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.window.size == 5

    def test_pass_rate_all_passed(self):
        for _ in range(4):
            self.window.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.window.pass_rate == 1.0

    def test_pass_rate_none_passed(self):
        for _ in range(3):
            self.window.record(_make_result("db.ping", CheckStatus.FAILED))
        assert self.window.pass_rate == 0.0

    def test_pass_rate_mixed(self):
        self.window.record(_make_result("db.ping", CheckStatus.PASSED))
        self.window.record(_make_result("db.ping", CheckStatus.FAILED))
        assert self.window.pass_rate == pytest.approx(0.5)

    def test_pass_rate_zero_when_empty(self):
        assert self.window.pass_rate == 0.0

    def test_is_degrading_true(self):
        for _ in range(3):
            self.window.record(_make_result("db.ping", CheckStatus.FAILED))
        assert self.window.is_degrading is True

    def test_is_degrading_false_when_last_passed(self):
        self.window.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.window.is_degrading is False

    def test_is_recovering(self):
        for _ in range(3):
            self.window.record(_make_result("db.ping", CheckStatus.FAILED))
        self.window.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.window.is_recovering is True

    def test_is_recovering_false_when_already_healthy(self):
        for _ in range(3):
            self.window.record(_make_result("db.ping", CheckStatus.PASSED))
        assert self.window.is_recovering is False

    def test_results_returns_copy(self):
        self.window.record(_make_result("db.ping", CheckStatus.PASSED))
        r = self.window.results
        r.clear()
        assert self.window.size == 1

    def test_repr_contains_name(self):
        assert "db.ping" in repr(self.window)


class TestTrendTracker:
    def setup_method(self):
        self.tracker = TrendTracker(max_size=5)

    def test_raises_on_zero_max_size(self):
        with pytest.raises(ValueError):
            TrendTracker(max_size=0)

    def test_max_size_stored(self):
        assert self.tracker.max_size == 5

    def test_get_returns_none_for_unknown(self):
        assert self.tracker.get("missing") is None

    def test_record_creates_window(self):
        self.tracker.record(_make_result("svc.health", CheckStatus.PASSED))
        assert self.tracker.get("svc.health") is not None

    def test_tracked_checks_lists_names(self):
        self.tracker.record(_make_result("a", CheckStatus.PASSED))
        self.tracker.record(_make_result("b", CheckStatus.FAILED))
        assert set(self.tracker.tracked_checks) == {"a", "b"}

    def test_degrading_checks(self):
        for _ in range(3):
            self.tracker.record(_make_result("bad", CheckStatus.FAILED))
        self.tracker.record(_make_result("good", CheckStatus.PASSED))
        assert "bad" in self.tracker.degrading_checks()
        assert "good" not in self.tracker.degrading_checks()

    def test_recovering_checks(self):
        for _ in range(3):
            self.tracker.record(_make_result("svc", CheckStatus.FAILED))
        self.tracker.record(_make_result("svc", CheckStatus.PASSED))
        assert "svc" in self.tracker.recovering_checks()

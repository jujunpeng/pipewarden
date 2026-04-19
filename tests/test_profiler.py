"""Tests for CheckProfiler."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.profiler import CheckProfiler, ProfileEntry


def _make_result(name: str, duration_ms: float, status: CheckStatus = CheckStatus.PASSED) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="ok",
        duration_ms=duration_ms,
    )


class TestProfileEntry:
    def test_is_slow_when_above_threshold(self):
        e = ProfileEntry("c", 500.0, 200.0)
        assert e.is_slow is True

    def test_not_slow_when_below_threshold(self):
        e = ProfileEntry("c", 100.0, 200.0)
        assert e.is_slow is False

    def test_not_slow_when_equal_threshold(self):
        e = ProfileEntry("c", 200.0, 200.0)
        assert e.is_slow is False

    def test_repr_contains_slow(self):
        e = ProfileEntry("c", 500.0, 200.0)
        assert "SLOW" in repr(e)

    def test_repr_contains_ok(self):
        e = ProfileEntry("c", 100.0, 200.0)
        assert "OK" in repr(e)


class TestCheckProfiler:
    def setup_method(self):
        self.profiler = CheckProfiler(threshold_ms=300.0)

    def test_raises_on_zero_threshold(self):
        with pytest.raises(ValueError):
            CheckProfiler(threshold_ms=0)

    def test_raises_on_negative_threshold(self):
        with pytest.raises(ValueError):
            CheckProfiler(threshold_ms=-1)

    def test_threshold_stored(self):
        assert self.profiler.threshold_ms == 300.0

    def test_initial_len_zero(self):
        assert len(self.profiler) == 0

    def test_observe_returns_entry(self):
        r = _make_result("check_a", 100.0)
        entry = self.profiler.observe(r)
        assert isinstance(entry, ProfileEntry)
        assert entry.check_name == "check_a"

    def test_observe_increments_len(self):
        self.profiler.observe(_make_result("a", 50.0))
        assert len(self.profiler) == 1

    def test_observe_raises_when_no_duration(self):
        r = CheckResult(check_name="x", status=CheckStatus.PASSED, message="ok")
        with pytest.raises(ValueError):
            self.profiler.observe(r)

    def test_slow_checks_empty_when_none_slow(self):
        self.profiler.observe(_make_result("a", 100.0))
        assert self.profiler.slow_checks() == []

    def test_slow_checks_returns_slow_entries(self):
        self.profiler.observe(_make_result("fast", 50.0))
        self.profiler.observe(_make_result("slow", 500.0))
        slow = self.profiler.slow_checks()
        assert len(slow) == 1
        assert slow[0].check_name == "slow"

    def test_all_entries_returns_copy(self):
        self.profiler.observe(_make_result("a", 100.0))
        entries = self.profiler.all_entries()
        entries.clear()
        assert len(self.profiler) == 1

    def test_reset_clears_entries(self):
        self.profiler.observe(_make_result("a", 100.0))
        self.profiler.reset()
        assert len(self.profiler) == 0

"""Tests for pipewarden.history."""

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.history import CheckHistory


def _make_result(name: str, status: CheckStatus, message: str = "") -> CheckResult:
    return CheckResult(check_name=name, status=status, message=message)


class TestCheckHistory:
    def setup_method(self):
        self.history = CheckHistory(max_size=5)

    # --- construction ---

    def test_default_max_size(self):
        h = CheckHistory()
        assert h.max_size == 100

    def test_custom_max_size(self):
        h = CheckHistory(max_size=10)
        assert h.max_size == 10

    def test_invalid_max_size_raises(self):
        with pytest.raises(ValueError):
            CheckHistory(max_size=0)

    # --- record / get ---

    def test_record_and_get(self):
        r = _make_result("check_a", CheckStatus.PASSED)
        self.history.record(r)
        results = self.history.get("check_a")
        assert len(results) == 1
        assert results[0] is r

    def test_get_unknown_check_returns_empty(self):
        assert self.history.get("nonexistent") == []

    def test_rolling_window_evicts_oldest(self):
        for i in range(6):
            self.history.record(_make_result("chk", CheckStatus.PASSED, str(i)))
        results = self.history.get("chk")
        assert len(results) == 5
        assert results[0].message == "1"
        assert results[-1].message == "5"

    # --- latest ---

    def test_latest_returns_most_recent(self):
        self.history.record(_make_result("chk", CheckStatus.PASSED, "first"))
        self.history.record(_make_result("chk", CheckStatus.FAILED, "second"))
        latest = self.history.latest("chk")
        assert latest is not None
        assert latest.message == "second"

    def test_latest_unknown_returns_none(self):
        assert self.history.latest("ghost") is None

    # --- known_checks ---

    def test_known_checks_sorted(self):
        self.history.record(_make_result("zebra", CheckStatus.PASSED))
        self.history.record(_make_result("alpha", CheckStatus.PASSED))
        assert self.history.known_checks() == ["alpha", "zebra"]

    # --- failure_rate ---

    def test_failure_rate_all_passed(self):
        for _ in range(4):
            self.history.record(_make_result("chk", CheckStatus.PASSED))
        assert self.history.failure_rate("chk") == 0.0

    def test_failure_rate_mixed(self):
        self.history.record(_make_result("chk", CheckStatus.PASSED))
        self.history.record(_make_result("chk", CheckStatus.FAILED))
        self.history.record(_make_result("chk", CheckStatus.ERROR))
        self.history.record(_make_result("chk", CheckStatus.PASSED))
        assert self.history.failure_rate("chk") == pytest.approx(0.5)

    def test_failure_rate_unknown_check_is_zero(self):
        assert self.history.failure_rate("nobody") == 0.0

    # --- clear ---

    def test_clear_specific_check(self):
        self.history.record(_make_result("chk", CheckStatus.PASSED))
        self.history.clear("chk")
        assert self.history.get("chk") == []

    def test_clear_all(self):
        self.history.record(_make_result("a", CheckStatus.PASSED))
        self.history.record(_make_result("b", CheckStatus.FAILED))
        self.history.clear()
        assert self.history.known_checks() == []

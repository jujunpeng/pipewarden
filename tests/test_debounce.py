"""Tests for pipewarden.debounce."""
from __future__ import annotations

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.debounce import DebounceAlert, DebounceNotifier


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="")


class TestDebounceNotifier:
    def setup_method(self) -> None:
        self.fired: list[DebounceAlert] = []
        self.notifier = DebounceNotifier(threshold=3)
        self.notifier.add_handler(self.fired.append)

    # --- construction ---

    def test_raises_on_zero_threshold(self) -> None:
        with pytest.raises(ValueError):
            DebounceNotifier(threshold=0)

    def test_raises_on_negative_threshold(self) -> None:
        with pytest.raises(ValueError):
            DebounceNotifier(threshold=-1)

    def test_threshold_stored(self) -> None:
        n = DebounceNotifier(threshold=2)
        assert n.threshold == 2

    def test_handler_count_starts_at_zero(self) -> None:
        assert DebounceNotifier(threshold=1).handler_count == 0

    def test_add_handler_increments_count(self) -> None:
        n = DebounceNotifier(threshold=1)
        n.add_handler(lambda a: None)
        assert n.handler_count == 1

    # --- observe: no alert before threshold ---

    def test_no_alert_before_threshold(self) -> None:
        r = _make_result("db", CheckStatus.FAILED)
        self.notifier.observe(r)
        self.notifier.observe(r)
        assert self.fired == []

    def test_alert_fires_exactly_at_threshold(self) -> None:
        r = _make_result("db", CheckStatus.FAILED)
        for _ in range(3):
            self.notifier.observe(r)
        assert len(self.fired) == 1

    def test_alert_fires_on_each_subsequent_failure(self) -> None:
        r = _make_result("db", CheckStatus.FAILED)
        for _ in range(5):
            self.notifier.observe(r)
        assert len(self.fired) == 3  # fires at 3, 4, 5

    def test_observe_returns_true_when_alert_fired(self) -> None:
        r = _make_result("db", CheckStatus.FAILED)
        self.notifier.observe(r)
        self.notifier.observe(r)
        result = self.notifier.observe(r)
        assert result is True

    def test_observe_returns_false_before_threshold(self) -> None:
        r = _make_result("db", CheckStatus.FAILED)
        assert self.notifier.observe(r) is False

    # --- passed result resets counter ---

    def test_passed_result_resets_counter(self) -> None:
        fail = _make_result("db", CheckStatus.FAILED)
        ok = _make_result("db", CheckStatus.PASSED)
        self.notifier.observe(fail)
        self.notifier.observe(fail)
        self.notifier.observe(ok)
        assert self.notifier.consecutive_failures("db") == 0

    def test_no_alert_after_reset_by_pass(self) -> None:
        fail = _make_result("db", CheckStatus.FAILED)
        ok = _make_result("db", CheckStatus.PASSED)
        self.notifier.observe(fail)
        self.notifier.observe(fail)
        self.notifier.observe(ok)
        # Two more failures — still below threshold again
        self.notifier.observe(fail)
        self.notifier.observe(fail)
        assert self.fired == []

    # --- error status counts as failure ---

    def test_error_status_counts_as_failure(self) -> None:
        r = _make_result("db", CheckStatus.ERROR)
        for _ in range(3):
            self.notifier.observe(r)
        assert len(self.fired) == 1

    # --- alert contents ---

    def test_alert_check_name(self) -> None:
        r = _make_result("payments", CheckStatus.FAILED)
        for _ in range(3):
            self.notifier.observe(r)
        assert self.fired[0].check_name == "payments"

    def test_alert_consecutive_failures(self) -> None:
        r = _make_result("payments", CheckStatus.FAILED)
        for _ in range(3):
            self.notifier.observe(r)
        assert self.fired[0].consecutive_failures == 3

    # --- manual reset ---

    def test_manual_reset_clears_counter(self) -> None:
        r = _make_result("db", CheckStatus.FAILED)
        self.notifier.observe(r)
        self.notifier.observe(r)
        self.notifier.reset("db")
        assert self.notifier.consecutive_failures("db") == 0

    def test_manual_reset_unknown_name_is_safe(self) -> None:
        self.notifier.reset("unknown")  # should not raise

    # --- independent counters per check ---

    def test_counters_are_independent_per_check(self) -> None:
        a = _make_result("a", CheckStatus.FAILED)
        b = _make_result("b", CheckStatus.FAILED)
        self.notifier.observe(a)
        self.notifier.observe(b)
        self.notifier.observe(a)
        assert self.notifier.consecutive_failures("a") == 2
        assert self.notifier.consecutive_failures("b") == 1

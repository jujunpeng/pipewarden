"""Tests for pipewarden.budget (ErrorBudget and BudgetViolation)."""
from datetime import datetime, timedelta

import pytest

from pipewarden.budget import BudgetViolation, ErrorBudget
from pipewarden.checks import CheckResult, CheckStatus


def _make_result(
    name: str = "db.check",
    status: CheckStatus = CheckStatus.FAILED,
    ts: datetime | None = None,
) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="",
        timestamp=ts or datetime(2024, 1, 1, 12, 0, 0),
        duration_ms=10.0,
    )


class TestErrorBudget:
    def setup_method(self):
        self.budget = ErrorBudget(
            check_name="db.check", max_failures=2, window_seconds=60.0
        )

    def test_raises_on_negative_max_failures(self):
        with pytest.raises(ValueError):
            ErrorBudget(check_name="x", max_failures=-1, window_seconds=60.0)

    def test_raises_on_zero_window(self):
        with pytest.raises(ValueError):
            ErrorBudget(check_name="x", max_failures=2, window_seconds=0)

    def test_raises_on_negative_window(self):
        with pytest.raises(ValueError):
            ErrorBudget(check_name="x", max_failures=2, window_seconds=-5)

    def test_initial_failure_count_is_zero(self):
        assert self.budget.failure_count == 0

    def test_not_exhausted_initially(self):
        assert not self.budget.exhausted

    def test_observe_failure_increments_count(self):
        self.budget.observe(_make_result(status=CheckStatus.FAILED))
        assert self.budget.failure_count == 1

    def test_observe_error_increments_count(self):
        self.budget.observe(_make_result(status=CheckStatus.ERROR))
        assert self.budget.failure_count == 1

    def test_observe_passed_does_not_increment(self):
        self.budget.observe(_make_result(status=CheckStatus.PASSED))
        assert self.budget.failure_count == 0

    def test_exhausted_when_over_budget(self):
        for _ in range(3):
            self.budget.observe(_make_result(status=CheckStatus.FAILED))
        assert self.budget.exhausted

    def test_not_exhausted_at_exact_budget(self):
        for _ in range(2):
            self.budget.observe(_make_result(status=CheckStatus.FAILED))
        assert not self.budget.exhausted

    def test_remaining_decreases(self):
        self.budget.observe(_make_result(status=CheckStatus.FAILED))
        assert self.budget.remaining == 1

    def test_remaining_zero_when_exhausted(self):
        for _ in range(5):
            self.budget.observe(_make_result(status=CheckStatus.FAILED))
        assert self.budget.remaining == 0

    def test_violation_is_none_when_not_exhausted(self):
        self.budget.observe(_make_result(status=CheckStatus.FAILED))
        assert self.budget.violation() is None

    def test_violation_returned_when_exhausted(self):
        for _ in range(3):
            self.budget.observe(_make_result(status=CheckStatus.FAILED))
        v = self.budget.violation()
        assert isinstance(v, BudgetViolation)
        assert v.check_name == "db.check"
        assert v.budget == 2

    def test_old_failures_evicted_outside_window(self):
        base = datetime(2024, 1, 1, 12, 0, 0)
        old = _make_result(status=CheckStatus.FAILED, ts=base)
        self.budget.observe(old)
        assert self.budget.failure_count == 1
        # Observe a result far in the future — old entry should be evicted
        future = _make_result(
            status=CheckStatus.PASSED,
            ts=base + timedelta(seconds=120),
        )
        self.budget.observe(future)
        assert self.budget.failure_count == 0

    def test_reset_clears_history(self):
        for _ in range(3):
            self.budget.observe(_make_result(status=CheckStatus.FAILED))
        self.budget.reset()
        assert self.budget.failure_count == 0

    def test_wrong_check_name_raises(self):
        result = _make_result(name="other.check")
        with pytest.raises(ValueError):
            self.budget.observe(result)


class TestBudgetViolation:
    def test_repr_contains_check_name(self):
        v = BudgetViolation(
            check_name="db.check",
            failures_observed=5,
            budget=3,
            window_seconds=60.0,
        )
        assert "db.check" in repr(v)
        assert "5" in repr(v)
        assert "3" in repr(v)

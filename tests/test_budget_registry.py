"""Tests for pipewarden.budget_registry (BudgetRegistry)."""
from datetime import datetime

import pytest

from pipewarden.budget import BudgetViolation, ErrorBudget
from pipewarden.budget_registry import BudgetRegistry
from pipewarden.checks import CheckResult, CheckStatus


def _make_result(
    name: str = "svc.check",
    status: CheckStatus = CheckStatus.FAILED,
    ts: datetime | None = None,
) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="",
        timestamp=ts or datetime(2024, 6, 1, 8, 0, 0),
        duration_ms=5.0,
    )


class TestBudgetRegistry:
    def setup_method(self):
        self.registry = BudgetRegistry(
            default_max_failures=2, default_window_seconds=300.0
        )

    def test_raises_on_negative_default_max_failures(self):
        with pytest.raises(ValueError):
            BudgetRegistry(default_max_failures=-1)

    def test_raises_on_zero_default_window(self):
        with pytest.raises(ValueError):
            BudgetRegistry(default_window_seconds=0)

    def test_raises_on_negative_default_window(self):
        with pytest.raises(ValueError):
            BudgetRegistry(default_window_seconds=-10)

    def test_default_max_failures_stored(self):
        assert self.registry.default_max_failures == 2

    def test_default_window_seconds_stored(self):
        assert self.registry.default_window_seconds == 300.0

    def test_get_returns_none_before_any_observation(self):
        assert self.registry.get("svc.check") is None

    def test_observe_creates_budget_lazily(self):
        self.registry.observe(_make_result())
        assert self.registry.get("svc.check") is not None

    def test_observe_uses_default_settings(self):
        self.registry.observe(_make_result())
        budget = self.registry.get("svc.check")
        assert budget.max_failures == 2
        assert budget.window_seconds == 300.0

    def test_no_violations_when_within_budget(self):
        self.registry.observe(_make_result(status=CheckStatus.FAILED))
        assert self.registry.violations() == []

    def test_violation_when_budget_exhausted(self):
        for _ in range(3):
            self.registry.observe(_make_result(status=CheckStatus.FAILED))
        violations = self.registry.violations()
        assert len(violations) == 1
        assert isinstance(violations[0], BudgetViolation)

    def test_set_budget_overrides_defaults(self):
        self.registry.set_budget("svc.check", max_failures=10, window_seconds=600.0)
        budget = self.registry.get("svc.check")
        assert budget is not None
        assert budget.max_failures == 10
        assert budget.window_seconds == 600.0

    def test_reset_clears_failures(self):
        for _ in range(3):
            self.registry.observe(_make_result(status=CheckStatus.FAILED))
        self.registry.reset("svc.check")
        assert self.registry.get("svc.check").failure_count == 0

    def test_reset_unknown_check_is_noop(self):
        self.registry.reset("nonexistent")

    def test_multiple_checks_tracked_independently(self):
        for _ in range(3):
            self.registry.observe(_make_result(name="a", status=CheckStatus.FAILED))
        self.registry.observe(_make_result(name="b", status=CheckStatus.PASSED))
        violations = self.registry.violations()
        names = [v.check_name for v in violations]
        assert "a" in names
        assert "b" not in names

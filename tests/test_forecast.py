"""Tests for pipewarden.forecast and pipewarden.forecast_registry."""
from __future__ import annotations

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.forecast import CheckForecaster, ForecastPoint
from pipewarden.forecast_registry import ForecastRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status)


# ---------------------------------------------------------------------------
# ForecastPoint
# ---------------------------------------------------------------------------

class TestForecastPoint:
    def test_repr_contains_step_and_rate(self):
        fp = ForecastPoint(step=2, failure_rate=0.25)
        assert "step=2" in repr(fp)
        assert "failure_rate" in repr(fp)


# ---------------------------------------------------------------------------
# CheckForecaster
# ---------------------------------------------------------------------------

class TestCheckForecaster:
    def setup_method(self):
        self.fc = CheckForecaster(check_name="db.ping", alpha=0.5, horizon=3)

    def test_raises_on_alpha_zero(self):
        with pytest.raises(ValueError, match="alpha"):
            CheckForecaster(check_name="x", alpha=0.0)

    def test_raises_on_alpha_above_one(self):
        with pytest.raises(ValueError, match="alpha"):
            CheckForecaster(check_name="x", alpha=1.1)

    def test_raises_on_horizon_less_than_one(self):
        with pytest.raises(ValueError, match="horizon"):
            CheckForecaster(check_name="x", horizon=0)

    def test_initial_smoothed_is_none(self):
        assert self.fc.smoothed_failure_rate is None

    def test_initial_total_observed_is_zero(self):
        assert self.fc.total_observed == 0

    def test_forecast_before_any_observation_is_zero(self):
        points = self.fc.forecast()
        assert len(points) == 3
        assert all(p.failure_rate == 0.0 for p in points)

    def test_observe_increments_total(self):
        self.fc.observe(_make_result("db.ping", CheckStatus.PASSED))
        assert self.fc.total_observed == 1

    def test_observe_wrong_check_raises(self):
        with pytest.raises(ValueError, match="db.ping"):
            self.fc.observe(_make_result("other", CheckStatus.FAILED))

    def test_first_failure_sets_smoothed_to_one(self):
        self.fc.observe(_make_result("db.ping", CheckStatus.FAILED))
        assert self.fc.smoothed_failure_rate == 1.0

    def test_first_pass_sets_smoothed_to_zero(self):
        self.fc.observe(_make_result("db.ping", CheckStatus.PASSED))
        assert self.fc.smoothed_failure_rate == 0.0

    def test_smoothing_blends_observations(self):
        # alpha=0.5; observe FAILED then PASSED
        self.fc.observe(_make_result("db.ping", CheckStatus.FAILED))  # smoothed=1.0
        self.fc.observe(_make_result("db.ping", CheckStatus.PASSED))  # smoothed=0.5
        assert self.fc.smoothed_failure_rate == pytest.approx(0.5)

    def test_forecast_returns_correct_horizon_length(self):
        self.fc.observe(_make_result("db.ping", CheckStatus.FAILED))
        points = self.fc.forecast()
        assert len(points) == 3

    def test_forecast_steps_are_sequential(self):
        points = self.fc.forecast()
        assert [p.step for p in points] == [1, 2, 3]

    def test_forecast_constant_after_observations(self):
        # Exponential smoothing flat-lines at current estimate
        self.fc.observe(_make_result("db.ping", CheckStatus.FAILED))
        points = self.fc.forecast()
        rates = [p.failure_rate for p in points]
        assert rates[0] == rates[1] == rates[2]

    def test_reset_clears_state(self):
        self.fc.observe(_make_result("db.ping", CheckStatus.FAILED))
        self.fc.reset()
        assert self.fc.smoothed_failure_rate is None
        assert self.fc.total_observed == 0


# ---------------------------------------------------------------------------
# ForecastRegistry
# ---------------------------------------------------------------------------

class TestForecastRegistry:
    def setup_method(self):
        self.reg = ForecastRegistry(default_alpha=0.4, default_horizon=2)

    def test_raises_on_invalid_alpha(self):
        with pytest.raises(ValueError, match="default_alpha"):
            ForecastRegistry(default_alpha=0.0)

    def test_raises_on_invalid_horizon(self):
        with pytest.raises(ValueError, match="default_horizon"):
            ForecastRegistry(default_horizon=0)

    def test_default_properties_stored(self):
        assert self.reg.default_alpha == pytest.approx(0.4)
        assert self.reg.default_horizon == 2

    def test_check_names_empty_initially(self):
        assert self.reg.check_names == []

    def test_observe_creates_forecaster(self):
        self.reg.observe(_make_result("svc.health", CheckStatus.PASSED))
        assert "svc.health" in self.reg.check_names

    def test_forecast_returns_correct_length(self):
        self.reg.observe(_make_result("svc.health", CheckStatus.FAILED))
        points = self.reg.forecast("svc.health")
        assert len(points) == 2

    def test_forecast_unknown_check_returns_zeros(self):
        points = self.reg.forecast("unknown")
        assert all(p.failure_rate == 0.0 for p in points)

    def test_get_returns_forecaster_instance(self):
        fc = self.reg.get("svc.health")
        assert isinstance(fc, CheckForecaster)
        assert fc.check_name == "svc.health"

    def test_reset_clears_forecaster_state(self):
        self.reg.observe(_make_result("svc.health", CheckStatus.FAILED))
        self.reg.reset("svc.health")
        fc = self.reg.get("svc.health")
        assert fc.smoothed_failure_rate is None

    def test_multiple_checks_tracked_independently(self):
        self.reg.observe(_make_result("a", CheckStatus.FAILED))
        self.reg.observe(_make_result("b", CheckStatus.PASSED))
        assert self.reg.get("a").smoothed_failure_rate == 1.0
        assert self.reg.get("b").smoothed_failure_rate == 0.0

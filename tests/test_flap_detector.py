"""Tests for FlapDetector and FlapRegistry."""

from __future__ import annotations

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.flap_detector import FlapAlert, FlapDetector
from pipewarden.flap_registry import FlapRegistry


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="")


# ---------------------------------------------------------------------------
# FlapDetector
# ---------------------------------------------------------------------------


class TestFlapDetector:
    def setup_method(self) -> None:
        self.detector = FlapDetector(check_name="db", window_size=6, threshold=3)

    def test_raises_on_small_window(self) -> None:
        with pytest.raises(ValueError):
            FlapDetector(check_name="x", window_size=1, threshold=1)

    def test_raises_on_zero_threshold(self) -> None:
        with pytest.raises(ValueError):
            FlapDetector(check_name="x", window_size=6, threshold=0)

    def test_raises_when_threshold_equals_window(self) -> None:
        with pytest.raises(ValueError):
            FlapDetector(check_name="x", window_size=4, threshold=4)

    def test_check_name_stored(self) -> None:
        assert self.detector.check_name == "db"

    def test_window_size_stored(self) -> None:
        assert self.detector.window_size == 6

    def test_threshold_stored(self) -> None:
        assert self.detector.threshold == 3

    def test_no_alert_when_stable(self) -> None:
        for _ in range(6):
            alert = self.detector.observe(_make_result("db", CheckStatus.PASSED))
        assert alert is None

    def test_alert_on_flapping(self) -> None:
        statuses = [
            CheckStatus.PASSED,
            CheckStatus.FAILED,
            CheckStatus.PASSED,
            CheckStatus.FAILED,
        ]
        alert = None
        for s in statuses:
            alert = self.detector.observe(_make_result("db", s))
        assert isinstance(alert, FlapAlert)
        assert alert.check_name == "db"
        assert alert.transitions >= 3

    def test_wrong_check_name_raises(self) -> None:
        with pytest.raises(ValueError):
            self.detector.observe(_make_result("other", CheckStatus.PASSED))

    def test_reset_clears_window(self) -> None:
        for s in [CheckStatus.PASSED, CheckStatus.FAILED] * 3:
            self.detector.observe(_make_result("db", s))
        self.detector.reset()
        assert self.detector.transitions() == 0

    def test_repr_contains_check_name(self) -> None:
        assert "db" in repr(self.detector)

    def test_flap_alert_repr(self) -> None:
        alert = FlapAlert(check_name="db", transitions=4, window_size=6)
        assert "db" in repr(alert)
        assert "4" in repr(alert)


# ---------------------------------------------------------------------------
# FlapRegistry
# ---------------------------------------------------------------------------


class TestFlapRegistry:
    def setup_method(self) -> None:
        self.registry = FlapRegistry(default_window_size=6, default_threshold=3)

    def test_raises_on_small_default_window(self) -> None:
        with pytest.raises(ValueError):
            FlapRegistry(default_window_size=1)

    def test_raises_on_zero_default_threshold(self) -> None:
        with pytest.raises(ValueError):
            FlapRegistry(default_window_size=6, default_threshold=0)

    def test_raises_when_threshold_equals_window(self) -> None:
        with pytest.raises(ValueError):
            FlapRegistry(default_window_size=4, default_threshold=4)

    def test_defaults_stored(self) -> None:
        assert self.registry.default_window_size == 6
        assert self.registry.default_threshold == 3

    def test_check_names_empty_initially(self) -> None:
        assert self.registry.check_names == []

    def test_observe_creates_detector(self) -> None:
        self.registry.observe(_make_result("api", CheckStatus.PASSED))
        assert "api" in self.registry.check_names

    def test_get_returns_none_for_unknown(self) -> None:
        assert self.registry.get("unknown") is None

    def test_get_returns_detector_after_observe(self) -> None:
        self.registry.observe(_make_result("api", CheckStatus.PASSED))
        detector = self.registry.get("api")
        assert isinstance(detector, FlapDetector)

    def test_no_alert_for_stable_check(self) -> None:
        for _ in range(6):
            alert = self.registry.observe(_make_result("api", CheckStatus.PASSED))
        assert alert is None

    def test_alert_returned_on_flapping(self) -> None:
        statuses = [
            CheckStatus.PASSED,
            CheckStatus.FAILED,
            CheckStatus.PASSED,
            CheckStatus.FAILED,
        ]
        alert = None
        for s in statuses:
            alert = self.registry.observe(_make_result("api", s))
        assert isinstance(alert, FlapAlert)

    def test_reset_clears_single_detector(self) -> None:
        for s in [CheckStatus.PASSED, CheckStatus.FAILED] * 3:
            self.registry.observe(_make_result("api", s))
        self.registry.reset("api")
        assert self.registry.get("api").transitions() == 0

    def test_reset_all_clears_all_detectors(self) -> None:
        for name in ["a", "b"]:
            for s in [CheckStatus.PASSED, CheckStatus.FAILED] * 3:
                self.registry.observe(_make_result(name, s))
        self.registry.reset_all()
        for name in ["a", "b"]:
            assert self.registry.get(name).transitions() == 0

    def test_repr_contains_check_count(self) -> None:
        self.registry.observe(_make_result("api", CheckStatus.PASSED))
        assert "1" in repr(self.registry)

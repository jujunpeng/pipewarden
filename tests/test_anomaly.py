import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.anomaly import AnomalyDetector, AnomalyAlert
from pipewarden.anomaly_registry import AnomalyRegistry


def _make_result(check_name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=check_name, status=status, message="")


class TestAnomalyDetector:
    def setup_method(self):
        self.detector = AnomalyDetector(check_name="db", window_size=4, failure_rate_threshold=0.5)

    def test_raises_on_zero_window(self):
        with pytest.raises(ValueError):
            AnomalyDetector(check_name="x", window_size=0)

    def test_raises_on_invalid_threshold(self):
        with pytest.raises(ValueError):
            AnomalyDetector(check_name="x", failure_rate_threshold=0.0)

    def test_raises_on_wrong_check_name(self):
        r = _make_result("other", CheckStatus.PASSED)
        with pytest.raises(ValueError):
            self.detector.observe(r)

    def test_no_alert_before_window_full(self):
        for _ in range(3):
            alert = self.detector.observe(_make_result("db", CheckStatus.FAILED))
        assert alert is None

    def test_alert_when_failure_rate_met(self):
        for _ in range(2):
            self.detector.observe(_make_result("db", CheckStatus.PASSED))
        for _ in range(2):
            self.detector.observe(_make_result("db", CheckStatus.FAILED))
        alert = self.detector.observe(_make_result("db", CheckStatus.FAILED))
        assert alert is not None
        assert isinstance(alert, AnomalyAlert)
        assert alert.check_name == "db"

    def test_no_alert_when_below_threshold(self):
        for _ in range(4):
            self.detector.observe(_make_result("db", CheckStatus.PASSED))
        alert = self.detector.observe(_make_result("db", CheckStatus.FAILED))
        assert alert is None

    def test_reset_clears_history(self):
        for _ in range(4):
            self.detector.observe(_make_result("db", CheckStatus.FAILED))
        self.detector.reset()
        assert self.detector.history_size == 0

    def test_repr_contains_check_name(self):
        r = _make_result("db", CheckStatus.PASSED)
        alert = AnomalyAlert(check_name="db", reason="test", result=r)
        assert "db" in repr(alert)


class TestAnomalyRegistry:
    def setup_method(self):
        self.registry = AnomalyRegistry(default_window_size=4, default_failure_rate_threshold=0.5)

    def test_raises_on_invalid_window(self):
        with pytest.raises(ValueError):
            AnomalyRegistry(default_window_size=0)

    def test_raises_on_invalid_threshold(self):
        with pytest.raises(ValueError):
            AnomalyRegistry(default_failure_rate_threshold=0.0)

    def test_tracked_checks_empty_initially(self):
        assert self.registry.tracked_checks == []

    def test_observe_creates_detector(self):
        self.registry.observe(_make_result("api", CheckStatus.PASSED))
        assert "api" in self.registry.tracked_checks

    def test_observe_many_returns_alerts(self):
        results = [_make_result("svc", CheckStatus.FAILED)] * 4
        alerts = self.registry.observe_many(results)
        assert isinstance(alerts, list)

    def test_reset_all_clears_histories(self):
        self.registry.observe(_make_result("x", CheckStatus.FAILED))
        self.registry.reset_all()
        assert self.registry._detectors["x"].history_size == 0

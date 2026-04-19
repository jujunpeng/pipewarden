import pytest
from datetime import datetime, timezone, timedelta
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.stale_detector import StaleDetector, StaleAlert


def _make_result(name: str, ts: datetime) -> CheckResult:
    return CheckResult(check_name=name, status=CheckStatus.PASSED, timestamp=ts)


NOW = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestStaleDetector:
    def setup_method(self):
        self.detector = StaleDetector(default_threshold_seconds=60.0)

    def test_raises_on_zero_threshold(self):
        with pytest.raises(ValueError):
            StaleDetector(default_threshold_seconds=0)

    def test_raises_on_negative_threshold(self):
        with pytest.raises(ValueError):
            StaleDetector(default_threshold_seconds=-10)

    def test_default_threshold_stored(self):
        assert self.detector.default_threshold_seconds == 60.0

    def test_no_alert_when_check_unknown(self):
        assert self.detector.check_stale("missing", now=NOW) is None

    def test_no_alert_when_fresh(self):
        ts = NOW - timedelta(seconds=30)
        self.detector.observe(_make_result("c1", ts))
        assert self.detector.check_stale("c1", now=NOW) is None

    def test_alert_when_stale(self):
        ts = NOW - timedelta(seconds=120)
        self.detector.observe(_make_result("c1", ts))
        alert = self.detector.check_stale("c1", now=NOW)
        assert isinstance(alert, StaleAlert)
        assert alert.check_name == "c1"
        assert alert.age_seconds > 60

    def test_alert_threshold_exact_boundary(self):
        ts = NOW - timedelta(seconds=60)
        self.detector.observe(_make_result("c1", ts))
        assert self.detector.check_stale("c1", now=NOW) is None

    def test_set_override_threshold(self):
        self.detector.set_threshold("c1", 200.0)
        ts = NOW - timedelta(seconds=120)
        self.detector.observe(_make_result("c1", ts))
        assert self.detector.check_stale("c1", now=NOW) is None

    def test_set_override_raises_on_invalid(self):
        with pytest.raises(ValueError):
            self.detector.set_threshold("c1", -5)

    def test_scan_returns_all_stale(self):
        self.detector.observe(_make_result("c1", NOW - timedelta(seconds=120)))
        self.detector.observe(_make_result("c2", NOW - timedelta(seconds=10)))
        alerts = self.detector.scan(now=NOW)
        names = [a.check_name for a in alerts]
        assert "c1" in names
        assert "c2" not in names

    def test_scan_empty_when_no_checks(self):
        assert self.detector.scan(now=NOW) == []

    def test_known_checks_after_observe(self):
        self.detector.observe(_make_result("c1", NOW))
        self.detector.observe(_make_result("c2", NOW))
        assert set(self.detector.known_checks()) == {"c1", "c2"}

    def test_repr_contains_check_name(self):
        alert = StaleAlert("my_check", NOW, 90.0, 60.0)
        assert "my_check" in repr(alert)
        assert "90.0" in repr(alert)

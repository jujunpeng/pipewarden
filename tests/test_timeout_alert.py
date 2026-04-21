"""Tests for pipewarden.timeout_alert."""
import pytest

from pipewarden.alerts import AlertHandler
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.timeout import TimeoutMonitor, TimeoutPolicy
from pipewarden.timeout_alert import TimeoutAlertHandler, TimeoutBreachAlert


def _make_result(duration_ms: float = 200.0) -> CheckResult:
    return CheckResult(check_name="slow_check", status=CheckStatus.PASSED, duration_ms=duration_ms)


class _CapturingHandler(AlertHandler):
    def __init__(self):
        self.received: list[CheckResult] = []

    def send(self, result: CheckResult) -> None:
        self.received.append(result)


def _make_handler(limit_ms: float = 100.0) -> tuple[TimeoutAlertHandler, _CapturingHandler]:
    monitor = TimeoutMonitor()
    monitor.add_policy(TimeoutPolicy(limit_ms=limit_ms))
    alert_handler = TimeoutAlertHandler(monitor=monitor)
    capturing = _CapturingHandler()
    alert_handler.add_handler(capturing)
    return alert_handler, capturing


class TestTimeoutAlertHandler:
    def test_raises_on_invalid_monitor(self):
        with pytest.raises(TypeError):
            TimeoutAlertHandler(monitor="not-a-monitor")  # type: ignore

    def test_raises_on_invalid_handler(self):
        monitor = TimeoutMonitor()
        h = TimeoutAlertHandler(monitor=monitor)
        with pytest.raises(TypeError):
            h.add_handler("bad")  # type: ignore

    def test_initial_handler_count_is_zero(self):
        monitor = TimeoutMonitor()
        h = TimeoutAlertHandler(monitor=monitor)
        assert h.handler_count == 0

    def test_add_handler_increments_count(self):
        monitor = TimeoutMonitor()
        h = TimeoutAlertHandler(monitor=monitor)
        h.add_handler(_CapturingHandler())
        assert h.handler_count == 1

    def test_observe_fires_alert_on_breach(self):
        handler, capturing = _make_handler(limit_ms=50.0)
        result = _make_result(duration_ms=200.0)
        alerts = handler.observe(result)
        assert len(alerts) == 1
        assert isinstance(alerts[0], TimeoutBreachAlert)
        assert len(capturing.received) == 1

    def test_observe_no_alert_within_limit(self):
        handler, capturing = _make_handler(limit_ms=500.0)
        result = _make_result(duration_ms=100.0)
        alerts = handler.observe(result)
        assert alerts == []
        assert capturing.received == []

    def test_breach_alert_contains_correct_violation(self):
        handler, _ = _make_handler(limit_ms=50.0)
        result = _make_result(duration_ms=300.0)
        alerts = handler.observe(result)
        assert alerts[0].violation.limit_ms == 50.0
        assert alerts[0].violation.duration_ms == 300.0
        assert alerts[0].result is result

    def test_multiple_handlers_all_notified(self):
        monitor = TimeoutMonitor()
        monitor.add_policy(TimeoutPolicy(limit_ms=10.0))
        h = TimeoutAlertHandler(monitor=monitor)
        c1, c2 = _CapturingHandler(), _CapturingHandler()
        h.add_handler(c1)
        h.add_handler(c2)
        h.observe(_make_result(duration_ms=999.0))
        assert len(c1.received) == 1
        assert len(c2.received) == 1

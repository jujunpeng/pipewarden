import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.sla import SLAPolicy, SLAMonitor
from pipewarden.sla_alert import SLAAlertHandler, SLABreachAlert
from pipewarden.alerts import AlertHandler


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="")


class _CapturingHandler(AlertHandler):
    def __init__(self):
        self.received = []

    def send(self, result: CheckResult) -> None:
        self.received.append(result)


def _make_monitor(pass_rate: float = 0.8, window: int = 3) -> SLAMonitor:
    monitor = SLAMonitor()
    monitor.add_policy(
        SLAPolicy(check_name="svc", required_pass_rate=pass_rate, window_size=window)
    )
    return monitor


class TestSLAAlertHandler:
    def setup_method(self):
        self.monitor = _make_monitor()
        self.handler = SLAAlertHandler(self.monitor)
        self.capture = _CapturingHandler()
        self.handler.add_handler(self.capture)

    def test_raises_on_invalid_monitor(self):
        with pytest.raises(TypeError):
            SLAAlertHandler("not-a-monitor")

    def test_handler_count_after_add(self):
        assert self.handler.handler_count == 1

    def test_breach_count_starts_at_zero(self):
        assert self.handler.breach_count == 0

    def test_no_alert_before_window_full(self):
        for _ in range(2):
            self.handler.observe(_make_result("svc", CheckStatus.FAILED))
        assert self.handler.breach_count == 0
        assert len(self.capture.received) == 0

    def test_alert_fired_on_sla_breach(self):
        for _ in range(3):
            self.handler.observe(_make_result("svc", CheckStatus.FAILED))
        assert self.handler.breach_count == 1
        assert len(self.capture.received) == 1

    def test_no_alert_when_sla_met(self):
        for _ in range(3):
            self.handler.observe(_make_result("svc", CheckStatus.PASSED))
        assert self.handler.breach_count == 0
        assert len(self.capture.received) == 0

    def test_alert_result_is_failed_status(self):
        for _ in range(3):
            self.handler.observe(_make_result("svc", CheckStatus.FAILED))
        assert self.capture.received[0].status == CheckStatus.FAILED

    def test_sla_breach_alert_repr(self):
        from pipewarden.sla import SLAViolation
        from datetime import datetime
        v = SLAViolation(
            check_name="svc",
            required_pass_rate=0.9,
            actual_pass_rate=0.5,
            window_size=10,
        )
        alert = SLABreachAlert(violation=v)
        assert "svc" in repr(alert)
        assert "SLABreachAlert" in repr(alert)

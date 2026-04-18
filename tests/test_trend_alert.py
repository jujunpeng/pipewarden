import pytest
from datetime import datetime
from unittest.mock import MagicMock
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.trend import TrendTracker
from pipewarden.trend_alert import TrendAlert, TrendAlertHandler


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="",
        duration_ms=1.0,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def tracker():
    return TrendTracker(max_size=5)


@pytest.fixture
def handler(tracker):
    return TrendAlertHandler(tracker)


class TestTrendAlert:
    def test_repr_contains_kind(self):
        a = TrendAlert(check_name="x", kind="degrading", pass_rate=0.2, window_size=5)
        assert "degrading" in repr(a)
        assert "x" in repr(a)


class TestTrendAlertHandler:
    def test_initial_handler_count_zero(self, handler):
        assert handler.handler_count == 0

    def test_add_handler_increments_count(self, handler):
        handler.add_handler(MagicMock())
        assert handler.handler_count == 1

    def test_observe_returns_none_when_healthy(self, handler):
        result = handler.observe(_make_result("svc", CheckStatus.PASSED))
        assert result is None

    def test_observe_returns_degrading_alert(self, handler):
        for _ in range(4):
            handler.observe(_make_result("svc", CheckStatus.FAILED))
        alert = handler.observe(_make_result("svc", CheckStatus.FAILED))
        assert alert is not None
        assert alert.kind == "degrading"
        assert alert.check_name == "svc"

    def test_observe_returns_recovering_alert(self, handler):
        for _ in range(4):
            handler.observe(_make_result("svc", CheckStatus.FAILED))
        alert = handler.observe(_make_result("svc", CheckStatus.PASSED))
        assert alert is not None
        assert alert.kind == "recovering"

    def test_alert_pass_rate_matches_window(self, handler):
        for _ in range(4):
            handler.observe(_make_result("svc", CheckStatus.FAILED))
        alert = handler.observe(_make_result("svc", CheckStatus.FAILED))
        assert alert is not None
        assert alert.pass_rate == pytest.approx(0.0)

    def test_handlers_called_on_alert(self, tracker):
        mock_handler = MagicMock()
        h = TrendAlertHandler(tracker, handlers=[mock_handler])
        for _ in range(4):
            h.observe(_make_result("svc", CheckStatus.FAILED))
        h.observe(_make_result("svc", CheckStatus.FAILED))
        assert mock_handler.send.called

    def test_handler_exception_does_not_propagate(self, tracker):
        bad = MagicMock()
        bad.send.side_effect = RuntimeError("boom")
        h = TrendAlertHandler(tracker, handlers=[bad])
        for _ in range(4):
            h.observe(_make_result("svc", CheckStatus.FAILED))
        # should not raise
        h.observe(_make_result("svc", CheckStatus.FAILED))

    def test_window_size_in_alert(self, handler):
        for _ in range(3):
            handler.observe(_make_result("svc", CheckStatus.FAILED))
        alert = handler.observe(_make_result("svc", CheckStatus.FAILED))
        assert alert is not None
        assert alert.window_size == 4

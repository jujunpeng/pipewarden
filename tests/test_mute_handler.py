"""Tests for pipewarden.mute_handler (MutedAlertHandler)."""
import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.mute import MuteRegistry, MuteRule
from pipewarden.mute_handler import MutedAlertHandler


def _make_result(name: str = "check_a", status: CheckStatus = CheckStatus.FAILED) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="msg")


class _CapturingHandler:
    def __init__(self):
        self.received = []

    def send(self, result: CheckResult) -> None:
        self.received.append(result)


class TestMutedAlertHandler:
    def setup_method(self):
        self.inner = _CapturingHandler()
        self.registry = MuteRegistry()
        self.handler = MutedAlertHandler(self.inner, self.registry)

    def test_raises_on_invalid_handler(self):
        with pytest.raises(TypeError):
            MutedAlertHandler("not-a-handler", self.registry)  # type: ignore

    def test_raises_on_invalid_registry(self):
        with pytest.raises(TypeError):
            MutedAlertHandler(self.inner, "not-a-registry")  # type: ignore

    def test_initial_suppressed_count_is_zero(self):
        assert self.handler.suppressed_count == 0

    def test_send_forwards_when_not_muted(self):
        result = _make_result()
        self.handler.send(result)
        assert len(self.inner.received) == 1
        assert self.inner.received[0] is result

    def test_send_suppresses_when_muted(self):
        self.registry.add(MuteRule("r", lambda r: True))
        self.handler.send(_make_result())
        assert len(self.inner.received) == 0

    def test_suppressed_count_increments_on_mute(self):
        self.registry.add(MuteRule("r", lambda r: True))
        self.handler.send(_make_result())
        self.handler.send(_make_result())
        assert self.handler.suppressed_count == 2

    def test_suppressed_count_unchanged_on_forwarded_send(self):
        self.handler.send(_make_result())
        assert self.handler.suppressed_count == 0

    def test_reset_count_zeroes_suppressed(self):
        self.registry.add(MuteRule("r", lambda r: True))
        self.handler.send(_make_result())
        self.handler.reset_count()
        assert self.handler.suppressed_count == 0

    def test_muted_result_does_not_reach_inner_handler(self):
        self.registry.add(MuteRule("r", lambda r: r.check_name == "check_a"))
        self.handler.send(_make_result("check_a"))
        self.handler.send(_make_result("check_b"))
        assert len(self.inner.received) == 1
        assert self.inner.received[0].check_name == "check_b"

    def test_repr_contains_suppressed_count(self):
        assert "suppressed=0" in repr(self.handler)

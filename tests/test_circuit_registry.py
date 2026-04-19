import pytest
from pipewarden.circuit_registry import CircuitRegistry
from pipewarden.circuit_breaker import CircuitState
from pipewarden.checks import CheckResult, CheckStatus


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="")


class TestCircuitRegistry:
    def setup_method(self):
        self.reg = CircuitRegistry(default_failure_threshold=2, default_recovery_timeout_seconds=30.0)

    def test_raises_on_invalid_threshold(self):
        with pytest.raises(ValueError):
            CircuitRegistry(default_failure_threshold=0)

    def test_raises_on_invalid_timeout(self):
        with pytest.raises(ValueError):
            CircuitRegistry(default_recovery_timeout_seconds=0)

    def test_default_threshold_stored(self):
        assert self.reg.default_failure_threshold == 2

    def test_default_timeout_stored(self):
        assert self.reg.default_recovery_timeout_seconds == 30.0

    def test_get_creates_breaker(self):
        cb = self.reg.get("svc")
        assert cb.check_name == "svc"

    def test_get_returns_same_instance(self):
        assert self.reg.get("svc") is self.reg.get("svc")

    def test_len_tracks_unique_checks(self):
        self.reg.get("a")
        self.reg.get("b")
        assert len(self.reg) == 2

    def test_observe_opens_circuit_after_threshold(self):
        for _ in range(2):
            self.reg.observe(_make_result("svc", CheckStatus.FAILED))
        assert self.reg.is_open("svc") is True

    def test_open_circuits_lists_open_names(self):
        for _ in range(2):
            self.reg.observe(_make_result("svc", CheckStatus.FAILED))
        assert "svc" in self.reg.open_circuits()

    def test_open_circuits_empty_when_all_closed(self):
        self.reg.observe(_make_result("svc", CheckStatus.PASSED))
        assert self.reg.open_circuits() == []

    def test_reset_closes_circuit(self):
        for _ in range(2):
            self.reg.observe(_make_result("svc", CheckStatus.FAILED))
        self.reg.reset("svc")
        assert self.reg.is_open("svc") is False

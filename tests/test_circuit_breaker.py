import time
import pytest
from pipewarden.circuit_breaker import CircuitBreaker, CircuitState
from pipewarden.checks import CheckResult, CheckStatus


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="")


class TestCircuitBreaker:
    def setup_method(self):
        self.cb = CircuitBreaker(check_name="db", failure_threshold=3, recovery_timeout_seconds=60.0)

    def test_raises_on_zero_threshold(self):
        with pytest.raises(ValueError):
            CircuitBreaker(check_name="x", failure_threshold=0)

    def test_raises_on_negative_timeout(self):
        with pytest.raises(ValueError):
            CircuitBreaker(check_name="x", recovery_timeout_seconds=-1.0)

    def test_initial_state_is_closed(self):
        assert self.cb.state == CircuitState.CLOSED

    def test_initial_failure_count_is_zero(self):
        assert self.cb.failure_count == 0

    def test_passed_result_keeps_closed(self):
        self.cb.observe(_make_result("db", CheckStatus.PASSED))
        assert self.cb.state == CircuitState.CLOSED

    def test_failures_below_threshold_stay_closed(self):
        self.cb.observe(_make_result("db", CheckStatus.FAILED))
        self.cb.observe(_make_result("db", CheckStatus.FAILED))
        assert self.cb.state == CircuitState.CLOSED

    def test_failures_at_threshold_open_circuit(self):
        for _ in range(3):
            self.cb.observe(_make_result("db", CheckStatus.FAILED))
        assert self.cb.state == CircuitState.OPEN

    def test_is_open_returns_true_when_open(self):
        for _ in range(3):
            self.cb.observe(_make_result("db", CheckStatus.FAILED))
        assert self.cb.is_open() is True

    def test_pass_after_failures_resets_to_closed(self):
        for _ in range(3):
            self.cb.observe(_make_result("db", CheckStatus.FAILED))
        self.cb.observe(_make_result("db", CheckStatus.PASSED))
        assert self.cb.state == CircuitState.CLOSED
        assert self.cb.failure_count == 0

    def test_wrong_check_name_raises(self):
        with pytest.raises(ValueError):
            self.cb.observe(_make_result("other", CheckStatus.FAILED))

    def test_reset_clears_state(self):
        for _ in range(3):
            self.cb.observe(_make_result("db", CheckStatus.FAILED))
        self.cb.reset()
        assert self.cb.state == CircuitState.CLOSED
        assert self.cb.failure_count == 0

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(check_name="db", failure_threshold=1, recovery_timeout_seconds=0.01)
        cb.observe(_make_result("db", CheckStatus.FAILED))
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN

    def test_repr_contains_check_name(self):
        assert "db" in repr(self.cb)

"""Tests for pipewarden.escalation."""
import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.escalation import EscalationPolicy


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="msg")


class TestEscalationPolicy:
    def setup_method(self):
        self.escalated: list[CheckResult] = []
        self.policy = EscalationPolicy(
            threshold=3, handler=self.escalated.append
        )

    def test_raises_on_zero_threshold(self):
        with pytest.raises(ValueError):
            EscalationPolicy(threshold=0, handler=lambda r: None)

    def test_raises_on_negative_threshold(self):
        with pytest.raises(ValueError):
            EscalationPolicy(threshold=-1, handler=lambda r: None)

    def test_no_escalation_before_threshold(self):
        for _ in range(2):
            triggered = self.policy.observe(_make_result("c", CheckStatus.FAILED))
            assert not triggered
        assert self.escalated == []

    def test_escalation_at_threshold(self):
        for _ in range(3):
            self.policy.observe(_make_result("c", CheckStatus.FAILED))
        assert len(self.escalated) == 1

    def test_escalation_on_every_failure_after_threshold(self):
        for _ in range(5):
            self.policy.observe(_make_result("c", CheckStatus.FAILED))
        assert len(self.escalated) == 3

    def test_passed_resets_counter(self):
        for _ in range(2):
            self.policy.observe(_make_result("c", CheckStatus.FAILED))
        self.policy.observe(_make_result("c", CheckStatus.PASSED))
        assert self.policy.consecutive_failures("c") == 0
        assert self.escalated == []

    def test_passed_prevents_escalation(self):
        self.policy.observe(_make_result("c", CheckStatus.FAILED))
        self.policy.observe(_make_result("c", CheckStatus.PASSED))
        self.policy.observe(_make_result("c", CheckStatus.FAILED))
        self.policy.observe(_make_result("c", CheckStatus.FAILED))
        assert self.escalated == []

    def test_error_status_counts_as_failure(self):
        for _ in range(3):
            self.policy.observe(_make_result("c", CheckStatus.ERROR))
        assert len(self.escalated) == 1

    def test_independent_counters_per_check(self):
        self.policy.observe(_make_result("a", CheckStatus.FAILED))
        self.policy.observe(_make_result("b", CheckStatus.FAILED))
        assert self.policy.consecutive_failures("a") == 1
        assert self.policy.consecutive_failures("b") == 1

    def test_reset_clears_counter(self):
        for _ in range(2):
            self.policy.observe(_make_result("c", CheckStatus.FAILED))
        self.policy.reset("c")
        assert self.policy.consecutive_failures("c") == 0

    def test_observe_returns_false_on_pass(self):
        result = self.policy.observe(_make_result("c", CheckStatus.PASSED))
        assert result is False

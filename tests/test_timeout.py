"""Tests for pipewarden.timeout."""
import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.timeout import TimeoutMonitor, TimeoutPolicy, TimeoutViolation


def _make_result(check_name: str = "db_check", status: CheckStatus = CheckStatus.PASSED, duration_ms: float = 100.0) -> CheckResult:
    return CheckResult(check_name=check_name, status=status, duration_ms=duration_ms)


class TestTimeoutPolicy:
    def test_raises_on_zero_limit(self):
        with pytest.raises(ValueError):
            TimeoutPolicy(limit_ms=0)

    def test_raises_on_negative_limit(self):
        with pytest.raises(ValueError):
            TimeoutPolicy(limit_ms=-1)

    def test_no_violation_when_within_limit(self):
        policy = TimeoutPolicy(limit_ms=200.0)
        result = _make_result(duration_ms=150.0)
        assert policy.evaluate(result) is None

    def test_no_violation_when_equal_to_limit(self):
        policy = TimeoutPolicy(limit_ms=100.0)
        result = _make_result(duration_ms=100.0)
        assert policy.evaluate(result) is None

    def test_violation_when_exceeds_limit(self):
        policy = TimeoutPolicy(limit_ms=50.0)
        result = _make_result(duration_ms=200.0)
        violation = policy.evaluate(result)
        assert violation is not None
        assert isinstance(violation, TimeoutViolation)
        assert violation.check_name == "db_check"
        assert violation.duration_ms == 200.0
        assert violation.limit_ms == 50.0

    def test_no_violation_when_duration_is_none(self):
        policy = TimeoutPolicy(limit_ms=50.0)
        result = CheckResult(check_name="x", status=CheckStatus.PASSED, duration_ms=None)
        assert policy.evaluate(result) is None

    def test_scoped_policy_ignores_other_check(self):
        policy = TimeoutPolicy(limit_ms=50.0, check_name="specific_check")
        result = _make_result(check_name="other_check", duration_ms=999.0)
        assert policy.evaluate(result) is None

    def test_scoped_policy_fires_for_matching_check(self):
        policy = TimeoutPolicy(limit_ms=50.0, check_name="db_check")
        result = _make_result(check_name="db_check", duration_ms=999.0)
        assert policy.evaluate(result) is not None


class TestTimeoutMonitor:
    def setup_method(self):
        self.monitor = TimeoutMonitor()

    def test_initial_policy_count_is_zero(self):
        assert self.monitor.policy_count == 0

    def test_add_policy_increments_count(self):
        self.monitor.add_policy(TimeoutPolicy(limit_ms=100.0))
        assert self.monitor.policy_count == 1

    def test_raises_on_invalid_policy(self):
        with pytest.raises(TypeError):
            self.monitor.add_policy("not-a-policy")  # type: ignore

    def test_evaluate_returns_empty_when_no_policies(self):
        result = _make_result(duration_ms=9999.0)
        assert self.monitor.evaluate(result) == []

    def test_evaluate_returns_violation_on_breach(self):
        self.monitor.add_policy(TimeoutPolicy(limit_ms=50.0))
        result = _make_result(duration_ms=200.0)
        violations = self.monitor.evaluate(result)
        assert len(violations) == 1
        assert violations[0].check_name == "db_check"

    def test_evaluate_returns_no_violation_within_limit(self):
        self.monitor.add_policy(TimeoutPolicy(limit_ms=500.0))
        result = _make_result(duration_ms=100.0)
        assert self.monitor.evaluate(result) == []

    def test_multiple_policies_all_evaluated(self):
        self.monitor.add_policy(TimeoutPolicy(limit_ms=50.0))
        self.monitor.add_policy(TimeoutPolicy(limit_ms=80.0))
        result = _make_result(duration_ms=200.0)
        violations = self.monitor.evaluate(result)
        assert len(violations) == 2

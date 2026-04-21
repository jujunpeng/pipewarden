import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.sla import SLAPolicy, SLAMonitor, SLAViolation


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="")


class TestSLAPolicy:
    def test_valid_construction(self):
        p = SLAPolicy(check_name="db", required_pass_rate=0.9, window_size=5)
        assert p.check_name == "db"
        assert p.required_pass_rate == 0.9
        assert p.window_size == 5

    def test_raises_on_pass_rate_above_one(self):
        with pytest.raises(ValueError):
            SLAPolicy(check_name="x", required_pass_rate=1.1)

    def test_raises_on_negative_pass_rate(self):
        with pytest.raises(ValueError):
            SLAPolicy(check_name="x", required_pass_rate=-0.1)

    def test_raises_on_zero_window_size(self):
        with pytest.raises(ValueError):
            SLAPolicy(check_name="x", required_pass_rate=0.9, window_size=0)

    def test_repr_contains_check_name(self):
        p = SLAPolicy(check_name="mycheck", required_pass_rate=0.8)
        assert "mycheck" in repr(p)


class TestSLAMonitor:
    def setup_method(self):
        self.monitor = SLAMonitor()
        self.policy = SLAPolicy(check_name="svc", required_pass_rate=0.8, window_size=5)
        self.monitor.add_policy(self.policy)

    def test_policy_names_contains_added_policy(self):
        assert "svc" in self.monitor.policy_names()

    def test_no_violation_before_window_full(self):
        for _ in range(4):
            result = self.monitor.observe(_make_result("svc", CheckStatus.FAILED))
        assert result is None

    def test_no_violation_when_pass_rate_met(self):
        for _ in range(4):
            self.monitor.observe(_make_result("svc", CheckStatus.PASSED))
        result = self.monitor.observe(_make_result("svc", CheckStatus.PASSED))
        assert result is None

    def test_violation_when_pass_rate_below_threshold(self):
        for _ in range(4):
            self.monitor.observe(_make_result("svc", CheckStatus.FAILED))
        result = self.monitor.observe(_make_result("svc", CheckStatus.FAILED))
        assert isinstance(result, SLAViolation)
        assert result.check_name == "svc"
        assert result.actual_pass_rate == 0.0

    def test_violation_actual_rate_correct(self):
        self.monitor.observe(_make_result("svc", CheckStatus.PASSED))
        for _ in range(4):
            self.monitor.observe(_make_result("svc", CheckStatus.FAILED))
        # window: [P, F, F, F, F] -> 1/5 = 0.2 < 0.8
        violations = []
        for _ in range(5):
            v = self.monitor.observe(_make_result("svc", CheckStatus.FAILED))
            if v:
                violations.append(v)
        assert len(violations) > 0
        assert violations[-1].actual_pass_rate == 0.0

    def test_returns_none_for_unknown_check(self):
        result = self.monitor.observe(_make_result("unknown", CheckStatus.FAILED))
        assert result is None

    def test_reset_clears_history(self):
        for _ in range(5):
            self.monitor.observe(_make_result("svc", CheckStatus.FAILED))
        self.monitor.reset("svc")
        # After reset window is empty, no violation should trigger immediately
        result = self.monitor.observe(_make_result("svc", CheckStatus.FAILED))
        assert result is None

    def test_sla_violation_repr(self):
        for _ in range(5):
            v = self.monitor.observe(_make_result("svc", CheckStatus.FAILED))
        assert v is not None
        assert "svc" in repr(v)

import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.dependency import DependencyGuard, DependencyRule, DependencyViolation


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="ok")


class TestDependencyRule:
    def test_repr_contains_names(self):
        rule = DependencyRule(check_name="b", depends_on="a")
        assert "b" in repr(rule)
        assert "a" in repr(rule)

    def test_evaluate_true_when_upstream_passed(self):
        rule = DependencyRule(check_name="b", depends_on="a")
        result = _make_result("a", CheckStatus.PASSED)
        assert rule.evaluate(result) is True

    def test_evaluate_false_when_upstream_failed(self):
        rule = DependencyRule(check_name="b", depends_on="a")
        result = _make_result("a", CheckStatus.FAILED)
        assert rule.evaluate(result) is False

    def test_evaluate_false_on_condition_exception(self):
        rule = DependencyRule(check_name="b", depends_on="a", condition=lambda r: 1 / 0)
        result = _make_result("a", CheckStatus.PASSED)
        assert rule.evaluate(result) is False


class TestDependencyGuard:
    def setup_method(self):
        self.guard = DependencyGuard()

    def test_initial_rule_count_zero(self):
        assert self.guard.rule_count == 0

    def test_add_rule_increments_count(self):
        self.guard.add_rule(DependencyRule("b", "a"))
        assert self.guard.rule_count == 1

    def test_add_non_rule_raises(self):
        with pytest.raises(TypeError):
            self.guard.add_rule("not-a-rule")

    def test_no_violations_when_all_pass(self):
        self.guard.add_rule(DependencyRule("b", "a"))
        results = {
            "a": _make_result("a", CheckStatus.PASSED),
            "b": _make_result("b", CheckStatus.PASSED),
        }
        assert self.guard.evaluate(results) == []

    def test_violation_when_upstream_missing(self):
        self.guard.add_rule(DependencyRule("b", "a"))
        results = {"b": _make_result("b", CheckStatus.PASSED)}
        violations = self.guard.evaluate(results)
        assert len(violations) == 1
        assert violations[0].check_name == "b"
        assert violations[0].depends_on == "a"

    def test_violation_when_upstream_failed(self):
        self.guard.add_rule(DependencyRule("b", "a"))
        results = {
            "a": _make_result("a", CheckStatus.FAILED),
            "b": _make_result("b", CheckStatus.PASSED),
        }
        violations = self.guard.evaluate(results)
        assert len(violations) == 1

    def test_violation_repr(self):
        v = DependencyViolation("b", "a", "some reason")
        assert "b" in repr(v)
        assert "a" in repr(v)

    def test_clear_removes_rules(self):
        self.guard.add_rule(DependencyRule("b", "a"))
        self.guard.clear()
        assert self.guard.rule_count == 0

    def test_multiple_rules_multiple_violations(self):
        self.guard.add_rule(DependencyRule("b", "a"))
        self.guard.add_rule(DependencyRule("c", "a"))
        results = {"a": _make_result("a", CheckStatus.FAILED)}
        violations = self.guard.evaluate(results)
        assert len(violations) == 2

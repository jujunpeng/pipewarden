"""Tests for pipewarden.labeler."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.labeler import (
    LabelRule,
    ResultLabeler,
    PASS,
    WARN,
    CRITICAL,
    UNKNOWN,
)


def _make_result(name: str, status: CheckStatus, duration_ms: float = 10.0) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="", duration_ms=duration_ms)


class TestLabelRule:
    def test_matches_returns_true_when_condition_true(self):
        rule = LabelRule(severity=CRITICAL, condition=lambda r: r.status == CheckStatus.FAILED)
        result = _make_result("c", CheckStatus.FAILED)
        assert rule.matches(result) is True

    def test_matches_returns_false_when_condition_false(self):
        rule = LabelRule(severity=CRITICAL, condition=lambda r: r.status == CheckStatus.FAILED)
        result = _make_result("c", CheckStatus.PASSED)
        assert rule.matches(result) is False

    def test_matches_returns_false_on_exception(self):
        rule = LabelRule(severity=WARN, condition=lambda r: 1 / 0)
        result = _make_result("c", CheckStatus.PASSED)
        assert rule.matches(result) is False

    def test_repr_contains_severity(self):
        rule = LabelRule(severity=WARN, description="slow")
        assert "warn" in repr(rule)
        assert "slow" in repr(rule)


class TestResultLabeler:
    def setup_method(self):
        self.labeler = ResultLabeler(default_severity=UNKNOWN)

    def test_default_severity_stored(self):
        assert self.labeler.default_severity == UNKNOWN

    def test_raises_on_empty_default(self):
        with pytest.raises(ValueError):
            ResultLabeler(default_severity="")

    def test_initial_rule_count_zero(self):
        assert self.labeler.rule_count == 0

    def test_add_rule_increments_count(self):
        rule = LabelRule(severity=WARN, condition=lambda r: True)
        self.labeler.add_rule(rule)
        assert self.labeler.rule_count == 1

    def test_add_rule_raises_on_wrong_type(self):
        with pytest.raises(TypeError):
            self.labeler.add_rule("not-a-rule")  # type: ignore

    def test_label_returns_default_when_no_rules(self):
        result = _make_result("c", CheckStatus.PASSED)
        assert self.labeler.label(result) == UNKNOWN

    def test_label_returns_first_matching_severity(self):
        self.labeler.add_rule(LabelRule(CRITICAL, lambda r: r.status == CheckStatus.FAILED))
        self.labeler.add_rule(LabelRule(WARN, lambda r: r.status == CheckStatus.ERROR))
        assert self.labeler.label(_make_result("c", CheckStatus.FAILED)) == CRITICAL
        assert self.labeler.label(_make_result("c", CheckStatus.ERROR)) == WARN

    def test_label_pass_rule(self):
        self.labeler.add_rule(LabelRule(PASS, lambda r: r.status == CheckStatus.PASSED))
        result = _make_result("c", CheckStatus.PASSED)
        assert self.labeler.label(result) == PASS

    def test_label_all_returns_dict_keyed_by_name(self):
        self.labeler.add_rule(LabelRule(CRITICAL, lambda r: r.status == CheckStatus.FAILED))
        results = [
            _make_result("a", CheckStatus.PASSED),
            _make_result("b", CheckStatus.FAILED),
        ]
        labels = self.labeler.label_all(results)
        assert labels["a"] == UNKNOWN
        assert labels["b"] == CRITICAL

    def test_clear_removes_all_rules(self):
        self.labeler.add_rule(LabelRule(WARN, lambda r: True))
        self.labeler.clear()
        assert self.labeler.rule_count == 0

    def test_repr_contains_rule_count(self):
        self.labeler.add_rule(LabelRule(WARN, lambda r: True))
        assert "rules=1" in repr(self.labeler)

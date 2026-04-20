import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.dependency import DependencyGuard, DependencyRule
from pipewarden.dependency_report import DependencyReport


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="ok")


class TestDependencyReport:
    def _guard_with_rule(self):
        g = DependencyGuard()
        g.add_rule(DependencyRule("b", "a"))
        return g

    def test_raises_on_non_guard(self):
        with pytest.raises(TypeError):
            DependencyReport("not-a-guard", {})

    def test_passed_when_no_violations(self):
        guard = self._guard_with_rule()
        results = {
            "a": _make_result("a", CheckStatus.PASSED),
            "b": _make_result("b", CheckStatus.PASSED),
        }
        report = DependencyReport(guard, results)
        assert report.passed is True

    def test_not_passed_when_violations_exist(self):
        guard = self._guard_with_rule()
        results = {"b": _make_result("b", CheckStatus.PASSED)}
        report = DependencyReport(guard, results)
        assert report.passed is False

    def test_violations_returns_copy(self):
        guard = self._guard_with_rule()
        results = {"b": _make_result("b", CheckStatus.PASSED)}
        report = DependencyReport(guard, results)
        v1 = report.violations
        v2 = report.violations
        assert v1 == v2
        assert v1 is not v2

    def test_render_all_satisfied_message(self):
        guard = self._guard_with_rule()
        results = {
            "a": _make_result("a", CheckStatus.PASSED),
            "b": _make_result("b", CheckStatus.PASSED),
        }
        report = DependencyReport(guard, results)
        assert "satisfied" in report.render()

    def test_render_contains_violation_details(self):
        guard = self._guard_with_rule()
        results = {"b": _make_result("b", CheckStatus.PASSED)}
        report = DependencyReport(guard, results)
        rendered = report.render()
        assert "b" in rendered
        assert "a" in rendered

    def test_str_equals_render(self):
        guard = self._guard_with_rule()
        results = {}
        report = DependencyReport(guard, results)
        assert str(report) == report.render()

    def test_repr_contains_violation_count(self):
        guard = self._guard_with_rule()
        results = {}
        report = DependencyReport(guard, results)
        assert "1" in repr(report)

"""Tests for pipewarden.correlator."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.correlator import CorrelationGroup, CorrelationAlert, ResultCorrelator


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="msg")


def _all_failed(results):
    return all(r.status == CheckStatus.FAILED for r in results)


class TestCorrelationGroup:
    def test_repr_contains_name(self):
        g = CorrelationGroup("g1", ["a", "b"], _all_failed)
        assert "g1" in repr(g)

    def test_matches_true_when_condition_true(self):
        g = CorrelationGroup("g", ["a"], _all_failed)
        r = _make_result("a", CheckStatus.FAILED)
        assert g.matches([r]) is True

    def test_matches_false_when_condition_false(self):
        g = CorrelationGroup("g", ["a"], _all_failed)
        r = _make_result("a", CheckStatus.PASSED)
        assert g.matches([r]) is False

    def test_matches_false_on_exception(self):
        def bad(results): raise RuntimeError("oops")
        g = CorrelationGroup("g", ["a"], bad)
        assert g.matches([_make_result("a", CheckStatus.FAILED)]) is False


class TestResultCorrelator:
    def setup_method(self):
        self.correlator = ResultCorrelator()

    def test_initial_group_count_zero(self):
        assert self.correlator.group_count == 0

    def test_add_group_increments_count(self):
        g = CorrelationGroup("g", ["a"], _all_failed)
        self.correlator.add_group(g)
        assert self.correlator.group_count == 1

    def test_add_non_group_raises(self):
        with pytest.raises(TypeError):
            self.correlator.add_group("not a group")  # type: ignore

    def test_evaluate_returns_alert_when_triggered(self):
        g = CorrelationGroup("cascade", ["a", "b"], _all_failed)
        self.correlator.add_group(g)
        results = [_make_result("a", CheckStatus.FAILED), _make_result("b", CheckStatus.FAILED)]
        alerts = self.correlator.evaluate(results)
        assert len(alerts) == 1
        assert alerts[0].group_name == "cascade"

    def test_evaluate_no_alert_when_not_triggered(self):
        g = CorrelationGroup("cascade", ["a", "b"], _all_failed)
        self.correlator.add_group(g)
        results = [_make_result("a", CheckStatus.PASSED), _make_result("b", CheckStatus.FAILED)]
        alerts = self.correlator.evaluate(results)
        assert len(alerts) == 0

    def test_evaluate_skips_missing_checks(self):
        g = CorrelationGroup("g", ["a", "missing"], _all_failed)
        self.correlator.add_group(g)
        results = [_make_result("a", CheckStatus.FAILED)]
        alerts = self.correlator.evaluate(results)
        # only 'a' is relevant; condition applied to [a] — all failed -> True
        assert len(alerts) == 1

    def test_evaluate_empty_results_yields_no_alerts(self):
        g = CorrelationGroup("g", ["a"], _all_failed)
        self.correlator.add_group(g)
        assert self.correlator.evaluate([]) == []

    def test_clear_removes_all_groups(self):
        self.correlator.add_group(CorrelationGroup("g", ["a"], _all_failed))
        self.correlator.clear()
        assert self.correlator.group_count == 0

    def test_repr_contains_group_count(self):
        assert "0" in repr(self.correlator)

    def test_alert_repr_contains_group_name(self):
        r = _make_result("x", CheckStatus.FAILED)
        alert = CorrelationAlert("my_group", [r])
        assert "my_group" in repr(alert)

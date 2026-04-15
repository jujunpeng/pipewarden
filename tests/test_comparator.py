"""Tests for pipewarden.comparator."""
from datetime import datetime

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.comparator import CheckComparator, CheckDiff, SnapshotComparison
from pipewarden.snapshot import PipelineSnapshot


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="",
        duration_ms=10.0,
        timestamp=datetime(2024, 1, 1),
    )


def _make_snapshot(*pairs) -> PipelineSnapshot:
    results = [_make_result(name, status) for name, status in pairs]
    return PipelineSnapshot(results=results, captured_at=datetime(2024, 1, 1))


@pytest.fixture()
def comparator() -> CheckComparator:
    return CheckComparator()


class TestCheckDiff:
    def test_is_regression_passed_to_failed(self):
        d = CheckDiff("c", CheckStatus.PASSED, CheckStatus.FAILED)
        assert d.is_regression is True

    def test_is_regression_passed_to_error(self):
        d = CheckDiff("c", CheckStatus.PASSED, CheckStatus.ERROR)
        assert d.is_regression is True

    def test_is_not_regression_when_still_passing(self):
        d = CheckDiff("c", CheckStatus.PASSED, CheckStatus.PASSED)
        assert d.is_regression is False

    def test_is_recovery_failed_to_passed(self):
        d = CheckDiff("c", CheckStatus.FAILED, CheckStatus.PASSED)
        assert d.is_recovery is True

    def test_is_recovery_error_to_passed(self):
        d = CheckDiff("c", CheckStatus.ERROR, CheckStatus.PASSED)
        assert d.is_recovery is True

    def test_is_new_when_previous_none(self):
        d = CheckDiff("c", None, CheckStatus.PASSED)
        assert d.is_new is True
        assert d.is_removed is False

    def test_is_removed_when_current_none(self):
        d = CheckDiff("c", CheckStatus.PASSED, None)
        assert d.is_removed is True
        assert d.is_new is False


class TestCheckComparator:
    def test_no_diffs_when_snapshots_identical(self, comparator):
        snap = _make_snapshot(("a", CheckStatus.PASSED), ("b", CheckStatus.FAILED))
        result = comparator.compare(snap, snap)
        assert result.diffs == []

    def test_detects_regression(self, comparator):
        prev = _make_snapshot(("a", CheckStatus.PASSED))
        curr = _make_snapshot(("a", CheckStatus.FAILED))
        result = comparator.compare(prev, curr)
        assert len(result.regressions) == 1
        assert result.regressions[0].check_name == "a"

    def test_detects_recovery(self, comparator):
        prev = _make_snapshot(("a", CheckStatus.FAILED))
        curr = _make_snapshot(("a", CheckStatus.PASSED))
        result = comparator.compare(prev, curr)
        assert len(result.recoveries) == 1

    def test_detects_new_check(self, comparator):
        prev = _make_snapshot(("a", CheckStatus.PASSED))
        curr = _make_snapshot(("a", CheckStatus.PASSED), ("b", CheckStatus.PASSED))
        result = comparator.compare(prev, curr)
        assert len(result.new_checks) == 1
        assert result.new_checks[0].check_name == "b"

    def test_detects_removed_check(self, comparator):
        prev = _make_snapshot(("a", CheckStatus.PASSED), ("b", CheckStatus.PASSED))
        curr = _make_snapshot(("a", CheckStatus.PASSED))
        result = comparator.compare(prev, curr)
        assert len(result.removed_checks) == 1
        assert result.removed_checks[0].check_name == "b"

    def test_has_regressions_false_when_clean(self, comparator):
        snap = _make_snapshot(("a", CheckStatus.PASSED))
        result = comparator.compare(snap, snap)
        assert result.has_regressions is False

    def test_has_regressions_true_when_regression_present(self, comparator):
        prev = _make_snapshot(("a", CheckStatus.PASSED))
        curr = _make_snapshot(("a", CheckStatus.ERROR))
        result = comparator.compare(prev, curr)
        assert result.has_regressions is True

    def test_multiple_changes_in_one_comparison(self, comparator):
        prev = _make_snapshot(
            ("a", CheckStatus.PASSED),
            ("b", CheckStatus.FAILED),
            ("c", CheckStatus.PASSED),
        )
        curr = _make_snapshot(
            ("a", CheckStatus.FAILED),
            ("b", CheckStatus.PASSED),
            ("d", CheckStatus.PASSED),
        )
        result = comparator.compare(prev, curr)
        assert len(result.regressions) == 1
        assert len(result.recoveries) == 1
        assert len(result.new_checks) == 1
        assert len(result.removed_checks) == 1

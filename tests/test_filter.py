"""Tests for pipewarden.filter.CheckFilter."""

import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.filter import CheckFilter


def _make_result(
    name: str = "check",
    status: CheckStatus = CheckStatus.PASSED,
    message: str = None,
    duration_ms: float = None,
) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message=message,
        duration_ms=duration_ms,
    )


class TestCheckFilter:
    def setup_method(self):
        self.results = [
            _make_result("a", CheckStatus.PASSED, "all good", 10.0),
            _make_result("b", CheckStatus.FAILED, "row count mismatch", 25.0),
            _make_result("c", CheckStatus.ERROR, "connection error", 5.0),
            _make_result("a", CheckStatus.FAILED, "threshold exceeded", 50.0),
        ]
        self.cf = CheckFilter(self.results)

    def test_len(self):
        assert len(self.cf) == 4

    def test_results_returns_copy(self):
        results = self.cf.results
        results.clear()
        assert len(self.cf) == 4

    def test_passed_returns_only_passed(self):
        passed = self.cf.passed()
        assert len(passed) == 1
        assert all(r.status == CheckStatus.PASSED for r in passed)

    def test_failed_returns_only_failed(self):
        failed = self.cf.failed()
        assert len(failed) == 2
        assert all(r.status == CheckStatus.FAILED for r in failed)

    def test_errored_returns_only_errored(self):
        errored = self.cf.errored()
        assert len(errored) == 1
        assert errored[0].check_name == "c"

    def test_by_status_unknown_returns_empty(self):
        # Passing a valid but unrepresented status still works
        results = CheckFilter([]).by_status(CheckStatus.PASSED)
        assert results == []

    def test_by_check_name_returns_matching(self):
        matches = self.cf.by_check_name("a")
        assert len(matches) == 2
        assert all(r.check_name == "a" for r in matches)

    def test_by_check_name_no_match_returns_empty(self):
        assert self.cf.by_check_name("z") == []

    def test_with_message_containing_case_insensitive(self):
        matches = self.cf.with_message_containing("COUNT")
        assert len(matches) == 1
        assert matches[0].check_name == "b"

    def test_with_message_containing_no_match(self):
        assert self.cf.with_message_containing("xyz") == []

    def test_with_message_containing_skips_none_message(self):
        results = [_make_result("x", CheckStatus.PASSED, None)]
        cf = CheckFilter(results)
        assert cf.with_message_containing("anything") == []

    def test_above_duration_ms_filters_correctly(self):
        slow = self.cf.above_duration_ms(20.0)
        assert len(slow) == 2
        assert all(r.duration_ms > 20.0 for r in slow)

    def test_above_duration_ms_skips_none_duration(self):
        results = [_make_result("x", duration_ms=None)]
        cf = CheckFilter(results)
        assert cf.above_duration_ms(0.0) == []

    def test_empty_filter(self):
        cf = CheckFilter([])
        assert cf.passed() == []
        assert cf.failed() == []
        assert cf.errored() == []
        assert len(cf) == 0

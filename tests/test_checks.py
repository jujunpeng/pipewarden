"""Tests for pipewarden.checks module."""

import pytest

from pipewarden.checks import CheckResult, CheckStatus, HealthCheck


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------

class TestCheckResult:
    def test_passed_returns_true_for_passed_status(self):
        result = CheckResult(name="row_count", status=CheckStatus.PASSED)
        assert result.passed() is True

    def test_passed_returns_false_for_failed_status(self):
        result = CheckResult(name="row_count", status=CheckStatus.FAILED)
        assert result.passed() is False

    def test_passed_returns_false_for_error_status(self):
        result = CheckResult(name="row_count", status=CheckStatus.ERROR)
        assert result.passed() is False

    def test_timestamp_is_set_automatically(self):
        result = CheckResult(name="x", status=CheckStatus.PASSED)
        assert result.timestamp is not None


# ---------------------------------------------------------------------------
# HealthCheck construction
# ---------------------------------------------------------------------------

class TestHealthCheckInit:
    def test_raises_if_predicate_not_callable(self):
        with pytest.raises(TypeError, match="predicate must be callable"):
            HealthCheck(name="bad", predicate="not_a_function")  # type: ignore[arg-type]

    def test_default_failure_message_uses_name(self):
        check = HealthCheck(name="my_check", predicate=lambda: True)
        assert "my_check" in check.failure_message

    def test_custom_failure_message_is_stored(self):
        check = HealthCheck(name="c", predicate=lambda: False, failure_message="Custom msg")
        assert check.failure_message == "Custom msg"


# ---------------------------------------------------------------------------
# HealthCheck.run
# ---------------------------------------------------------------------------

class TestHealthCheckRun:
    def test_run_returns_passed_when_predicate_is_true(self):
        check = HealthCheck(name="always_pass", predicate=lambda: True)
        result = check.run()
        assert result.status == CheckStatus.PASSED
        assert result.passed() is True
        assert result.message == ""

    def test_run_returns_failed_when_predicate_is_false(self):
        check = HealthCheck(name="always_fail", predicate=lambda: False)
        result = check.run()
        assert result.status == CheckStatus.FAILED
        assert result.passed() is False
        assert result.message != ""

    def test_run_returns_error_when_predicate_raises(self):
        def boom():
            raise ValueError("something went wrong")

        check = HealthCheck(name="exploder", predicate=boom)
        result = check.run()
        assert result.status == CheckStatus.ERROR
        assert "something went wrong" in result.message

    def test_run_result_name_matches_check_name(self):
        check = HealthCheck(name="named_check", predicate=lambda: True)
        result = check.run()
        assert result.name == "named_check"

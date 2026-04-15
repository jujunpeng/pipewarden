"""Tests for pipewarden.retry."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from pipewarden.checks import CheckResult, CheckStatus, HealthCheck
from pipewarden.retry import RetryPolicy, RetryRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_check(statuses: list[CheckStatus]) -> HealthCheck:
    """Return a HealthCheck whose successive runs yield *statuses* in order."""
    results = [
        CheckResult(check_name="demo", status=s, message="") for s in statuses
    ]
    iterator = iter(results)
    check = MagicMock(spec=HealthCheck)
    check.name = "demo"
    check.run.side_effect = lambda: next(iterator)
    return check


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------

class TestRetryPolicy:
    def test_default_values(self):
        p = RetryPolicy()
        assert p.max_attempts == 3
        assert p.delay_seconds == 0.0

    def test_custom_values(self):
        p = RetryPolicy(max_attempts=5, delay_seconds=1.5)
        assert p.max_attempts == 5
        assert p.delay_seconds == 1.5

    def test_raises_on_zero_attempts(self):
        with pytest.raises(ValueError, match="max_attempts"):
            RetryPolicy(max_attempts=0)

    def test_raises_on_negative_attempts(self):
        with pytest.raises(ValueError, match="max_attempts"):
            RetryPolicy(max_attempts=-1)

    def test_raises_on_negative_delay(self):
        with pytest.raises(ValueError, match="delay_seconds"):
            RetryPolicy(delay_seconds=-0.1)


# ---------------------------------------------------------------------------
# RetryRunner
# ---------------------------------------------------------------------------

class TestRetryRunner:
    def test_returns_immediately_on_pass(self):
        check = _make_check([CheckStatus.PASSED])
        runner = RetryRunner(RetryPolicy(max_attempts=3))
        result = runner.run(check)
        assert result.status == CheckStatus.PASSED
        assert check.run.call_count == 1

    def test_retries_on_failure_and_eventually_passes(self):
        check = _make_check(
            [CheckStatus.FAILED, CheckStatus.FAILED, CheckStatus.PASSED]
        )
        runner = RetryRunner(RetryPolicy(max_attempts=3))
        result = runner.run(check)
        assert result.status == CheckStatus.PASSED
        assert check.run.call_count == 3

    def test_returns_last_result_when_all_attempts_fail(self):
        check = _make_check(
            [CheckStatus.FAILED, CheckStatus.FAILED, CheckStatus.FAILED]
        )
        runner = RetryRunner(RetryPolicy(max_attempts=3))
        result = runner.run(check)
        assert result.status == CheckStatus.FAILED
        assert check.run.call_count == 3

    def test_retries_on_error_status(self):
        check = _make_check([CheckStatus.ERROR, CheckStatus.PASSED])
        runner = RetryRunner(RetryPolicy(max_attempts=2))
        result = runner.run(check)
        assert result.status == CheckStatus.PASSED
        assert check.run.call_count == 2

    def test_sleep_called_between_retries(self):
        sleep_mock = MagicMock()
        check = _make_check(
            [CheckStatus.FAILED, CheckStatus.FAILED, CheckStatus.PASSED]
        )
        runner = RetryRunner(
            RetryPolicy(max_attempts=3, delay_seconds=0.5), sleep_fn=sleep_mock
        )
        runner.run(check)
        assert sleep_mock.call_count == 2
        sleep_mock.assert_has_calls([call(0.5), call(0.5)])

    def test_sleep_not_called_when_delay_is_zero(self):
        sleep_mock = MagicMock()
        check = _make_check([CheckStatus.FAILED, CheckStatus.PASSED])
        runner = RetryRunner(
            RetryPolicy(max_attempts=2, delay_seconds=0.0), sleep_fn=sleep_mock
        )
        runner.run(check)
        sleep_mock.assert_not_called()

    def test_policy_property(self):
        policy = RetryPolicy(max_attempts=2)
        runner = RetryRunner(policy)
        assert runner.policy is policy

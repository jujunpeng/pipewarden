"""Tests for pipewarden.runner.CheckRunner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipewarden.checks import CheckResult, CheckStatus, HealthCheck
from pipewarden.pipeline import Pipeline, PipelineReport
from pipewarden.runner import CheckRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_check(name: str, status: CheckStatus, message: str = "") -> HealthCheck:
    check = MagicMock(spec=HealthCheck)
    check.name = name
    check.run.return_value = CheckResult(
        check_name=name, status=status, message=message
    )
    return check


def _make_runner(*checks: HealthCheck, handlers=None) -> CheckRunner:
    return CheckRunner(checks=list(checks), alert_handlers=handlers or [])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCheckRunner:
    def test_run_returns_pipeline_report(self):
        check = _make_check("c1", CheckStatus.PASSED)
        runner = _make_runner(check)
        report = runner.run()
        assert isinstance(report, PipelineReport)

    def test_run_collects_all_results(self):
        checks = [
            _make_check("c1", CheckStatus.PASSED),
            _make_check("c2", CheckStatus.FAILED),
            _make_check("c3", CheckStatus.ERROR),
        ]
        runner = _make_runner(*checks)
        report = runner.run()
        assert len(report.results) == 3

    def test_run_passes_when_all_checks_pass(self):
        checks = [_make_check(f"c{i}", CheckStatus.PASSED) for i in range(3)]
        runner = _make_runner(*checks)
        report = runner.run()
        assert report.passed()

    def test_run_fails_when_any_check_fails(self):
        checks = [
            _make_check("c1", CheckStatus.PASSED),
            _make_check("c2", CheckStatus.FAILED),
        ]
        runner = _make_runner(*checks)
        report = runner.run()
        assert not report.passed()

    def test_exception_in_check_produces_error_result(self):
        check = MagicMock(spec=HealthCheck)
        check.name = "boom"
        check.run.side_effect = RuntimeError("kaboom")

        runner = _make_runner(check)
        report = runner.run()

        assert len(report.results) == 1
        result = report.results[0]
        assert result.status == CheckStatus.ERROR
        assert "kaboom" in result.message

    def test_alert_handlers_called_for_each_result(self):
        handler = MagicMock()
        checks = [
            _make_check("c1", CheckStatus.PASSED),
            _make_check("c2", CheckStatus.FAILED),
        ]
        runner = _make_runner(*checks, handlers=[handler])
        runner.run()
        assert handler.send.call_count == 2

    def test_failing_alert_handler_does_not_raise(self):
        handler = MagicMock()
        handler.send.side_effect = Exception("alert error")
        check = _make_check("c1", CheckStatus.FAILED)
        runner = _make_runner(check, handlers=[handler])
        # Should not raise
        runner.run()

    def test_empty_checks_returns_passing_report(self):
        runner = CheckRunner(checks=[])
        report = runner.run()
        assert report.passed()
        assert report.results == []

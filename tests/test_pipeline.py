"""Tests for pipewarden.pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewarden.checks import CheckResult, CheckStatus, HealthCheck
from pipewarden.pipeline import Pipeline, PipelineReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_check(name: str, status: CheckStatus, message: str = "") -> HealthCheck:
    """Return a HealthCheck whose run() returns a fixed result."""
    check = MagicMock(spec=HealthCheck)
    check.name = name
    check.run.return_value = CheckResult(check_name=name, status=status, message=message)
    return check


def _make_pipeline(*checks: HealthCheck) -> Pipeline:
    return Pipeline(name="test-pipeline", checks=list(checks))


# ---------------------------------------------------------------------------
# PipelineReport
# ---------------------------------------------------------------------------

class TestPipelineReport:
    def test_passed_when_all_checks_pass(self):
        report = PipelineReport(
            pipeline_name="p",
            results=[
                CheckResult("a", CheckStatus.PASSED),
                CheckResult("b", CheckStatus.PASSED),
            ],
        )
        assert report.passed is True

    def test_not_passed_when_any_check_fails(self):
        report = PipelineReport(
            pipeline_name="p",
            results=[
                CheckResult("a", CheckStatus.PASSED),
                CheckResult("b", CheckStatus.FAILED),
            ],
        )
        assert report.passed is False

    def test_failed_checks_filters_correctly(self):
        r1 = CheckResult("a", CheckStatus.FAILED)
        r2 = CheckResult("b", CheckStatus.PASSED)
        report = PipelineReport(pipeline_name="p", results=[r1, r2])
        assert report.failed_checks == [r1]

    def test_error_checks_filters_correctly(self):
        r1 = CheckResult("a", CheckStatus.ERROR)
        r2 = CheckResult("b", CheckStatus.PASSED)
        report = PipelineReport(pipeline_name="p", results=[r1, r2])
        assert report.error_checks == [r1]

    def test_summary_format(self):
        report = PipelineReport(
            pipeline_name="my-pipeline",
            results=[
                CheckResult("a", CheckStatus.PASSED),
                CheckResult("b", CheckStatus.FAILED),
            ],
        )
        assert "my-pipeline" in report.summary()
        assert "1/2" in report.summary()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class TestPipeline:
    def test_run_returns_report_with_all_results(self):
        c1 = _make_check("c1", CheckStatus.PASSED)
        c2 = _make_check("c2", CheckStatus.FAILED)
        pipeline = _make_pipeline(c1, c2)
        report = pipeline.run()
        assert len(report.results) == 2

    def test_run_dispatches_alerts_for_each_result(self):
        c1 = _make_check("c1", CheckStatus.FAILED)
        handler = MagicMock()
        pipeline = Pipeline(name="p", checks=[c1], alert_handlers=[handler])
        pipeline.run()
        handler.send.assert_called_once()

    def test_add_check_appends_check(self):
        pipeline = Pipeline(name="p")
        check = _make_check("c1", CheckStatus.PASSED)
        pipeline.add_check(check)
        assert check in pipeline.checks

    def test_add_alert_handler_appends_handler(self):
        pipeline = Pipeline(name="p")
        handler = MagicMock()
        pipeline.add_alert_handler(handler)
        assert handler in pipeline.alert_handlers

    def test_run_catches_unexpected_exception_as_error(self):
        broken_check = MagicMock(spec=HealthCheck)
        broken_check.name = "broken"
        broken_check.run.side_effect = RuntimeError("boom")
        pipeline = Pipeline(name="p", checks=[broken_check])
        report = pipeline.run()
        assert report.results[0].status == CheckStatus.ERROR
        assert "boom" in report.results[0].message

    def test_pipeline_report_name_matches(self):
        pipeline = Pipeline(name="my-etl")
        report = pipeline.run()
        assert report.pipeline_name == "my-etl"

"""Tests for pipewarden.reporter."""

from __future__ import annotations

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.metrics import MetricsCollector
from pipewarden.pipeline import PipelineReport
from pipewarden.reporter import PipelineReporter


def _make_result(
    name: str,
    status: CheckStatus = CheckStatus.PASSED,
    message: str = "",
    duration_ms: float = 5.0,
) -> CheckResult:
    return CheckResult(
        check_name=name, status=status, message=message, duration_ms=duration_ms
    )


def _make_report(*results: CheckResult) -> PipelineReport:
    return PipelineReport(results=list(results))


class TestPipelineReporter:
    def test_render_all_passed_label(self):
        report = _make_report(_make_result("check_a"))
        output = PipelineReporter(report).render()
        assert "PASSED" in output

    def test_render_failed_label_when_any_failed(self):
        report = _make_report(
            _make_result("check_a"),
            _make_result("check_b", status=CheckStatus.FAILED, message="row count low"),
        )
        output = PipelineReporter(report).render()
        assert "FAILED" in output

    def test_render_summary_counts(self):
        report = _make_report(
            _make_result("a"),
            _make_result("b", status=CheckStatus.FAILED),
            _make_result("c", status=CheckStatus.ERROR),
        )
        output = PipelineReporter(report).render()
        assert "Total: 3" in output
        assert "Passed: 1" in output
        assert "Failed: 1" in output
        assert "Errors: 1" in output

    def test_render_failed_checks_section(self):
        report = _make_report(
            _make_result("bad_check", status=CheckStatus.FAILED, message="too low")
        )
        output = PipelineReporter(report).render()
        assert "Failed checks" in output
        assert "bad_check" in output
        assert "too low" in output

    def test_render_error_checks_section(self):
        report = _make_report(
            _make_result("err_check", status=CheckStatus.ERROR, message="timeout")
        )
        output = PipelineReporter(report).render()
        assert "Error checks" in output
        assert "err_check" in output
        assert "timeout" in output

    def test_render_no_failed_section_when_all_pass(self):
        report = _make_report(_make_result("ok"))
        output = PipelineReporter(report).render()
        assert "Failed checks" not in output
        assert "Error checks" not in output

    def test_render_with_metrics(self):
        collector = MetricsCollector()
        collector.record(_make_result("check_a", duration_ms=20.0))
        collector.record(_make_result("check_a", status=CheckStatus.FAILED, duration_ms=30.0))
        report = _make_report(_make_result("check_a"))
        output = PipelineReporter(report, metrics=collector).render()
        assert "Historical metrics" in output
        assert "check_a" in output
        assert "pass_rate=50%" in output
        assert "avg_duration=25.0ms" in output
        assert "runs=2" in output

    def test_render_without_metrics_no_section(self):
        report = _make_report(_make_result("x"))
        output = PipelineReporter(report).render()
        assert "Historical metrics" not in output

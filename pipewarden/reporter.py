"""Human-readable report formatting for pipeline runs and metrics."""

from __future__ import annotations

from typing import Optional

from pipewarden.metrics import MetricsCollector
from pipewarden.pipeline import PipelineReport


class PipelineReporter:
    """Formats a PipelineReport (and optional metrics) as plain text."""

    def __init__(
        self,
        report: PipelineReport,
        metrics: Optional[MetricsCollector] = None,
    ) -> None:
        self._report = report
        self._metrics = metrics

    def render(self) -> str:
        """Return a multi-line string summarising the pipeline run."""
        lines: list[str] = []
        summary = self._report.summary()
        status_label = "PASSED" if self._report.passed() else "FAILED"

        lines.append(f"Pipeline Run — {status_label}")
        lines.append("-" * 40)
        lines.append(
            f"Total: {summary['total']}  "
            f"Passed: {summary['passed']}  "
            f"Failed: {summary['failed']}  "
            f"Errors: {summary['errors']}"
        )

        if self._report.failed_checks():
            lines.append("\nFailed checks:")
            for r in self._report.failed_checks():
                lines.append(f"  ✗ {r.check_name}: {r.message}")

        if self._report.error_checks():
            lines.append("\nError checks:")
            for r in self._report.error_checks():
                lines.append(f"  ! {r.check_name}: {r.message}")

        if self._metrics is not None:
            lines.append("\nHistorical metrics:")
            for name, m in sorted(self._metrics.all_metrics().items()):
                lines.append(
                    f"  {name}: pass_rate={m.pass_rate:.0%}  "
                    f"avg_duration={m.avg_duration_ms:.1f}ms  "
                    f"runs={m.total_runs}"
                )

        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover
        return self.render()

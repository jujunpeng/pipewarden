"""Pipeline runner that executes health checks and dispatches alerts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewarden.alerts import AlertHandler
from pipewarden.checks import CheckResult, CheckStatus, HealthCheck


@dataclass
class PipelineReport:
    """Aggregated result of running all checks in a pipeline."""

    pipeline_name: str
    results: List[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return True only when every check passed."""
        return all(r.status == CheckStatus.PASSED for r in self.results)

    @property
    def failed_checks(self) -> List[CheckResult]:
        return [r for r in self.results if r.status == CheckStatus.FAILED]

    @property
    def error_checks(self) -> List[CheckResult]:
        return [r for r in self.results if r.status == CheckStatus.ERROR]

    def summary(self) -> str:
        total = len(self.results)
        n_passed = sum(1 for r in self.results if r.status == CheckStatus.PASSED)
        return (
            f"Pipeline '{self.pipeline_name}': "
            f"{n_passed}/{total} checks passed"
        )


class Pipeline:
    """Runs a collection of :class:`HealthCheck` instances and alerts on issues."""

    def __init__(
        self,
        name: str,
        checks: Optional[List[HealthCheck]] = None,
        alert_handlers: Optional[List[AlertHandler]] = None,
    ) -> None:
        self.name = name
        self.checks: List[HealthCheck] = checks or []
        self.alert_handlers: List[AlertHandler] = alert_handlers or []

    def add_check(self, check: HealthCheck) -> None:
        """Register an additional health check."""
        self.checks.append(check)

    def add_alert_handler(self, handler: AlertHandler) -> None:
        """Register an additional alert handler."""
        self.alert_handlers.append(handler)

    def run(self) -> PipelineReport:
        """Execute all checks and dispatch alerts; return a :class:`PipelineReport`."""
        report = PipelineReport(pipeline_name=self.name)

        for check in self.checks:
            try:
                result: CheckResult = check.run()
            except Exception as exc:  # noqa: BLE001
                result = CheckResult(
                    check_name=check.name,
                    status=CheckStatus.ERROR,
                    message=f"Unexpected error: {exc}",
                )

            report.results.append(result)

            for handler in self.alert_handlers:
                handler.send(result)

        return report

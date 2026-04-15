"""Runner module for executing health checks and producing pipeline reports."""

from __future__ import annotations

import logging
from typing import Iterable, List, Optional

from .checks import CheckResult, CheckStatus, HealthCheck
from .pipeline import Pipeline, PipelineReport
from .alerts import AlertHandler

logger = logging.getLogger(__name__)


class CheckRunner:
    """Executes a collection of health checks and returns a PipelineReport."""

    def __init__(
        self,
        checks: Iterable[HealthCheck],
        alert_handlers: Optional[List[AlertHandler]] = None,
    ) -> None:
        self._checks: List[HealthCheck] = list(checks)
        self._alert_handlers: List[AlertHandler] = alert_handlers or []

    def run(self) -> PipelineReport:
        """Run all registered checks and return a PipelineReport."""
        results: List[CheckResult] = []

        for check in self._checks:
            try:
                result = check.run()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Unexpected error running check '%s'", check.name)
                result = CheckResult(
                    check_name=check.name,
                    status=CheckStatus.ERROR,
                    message=f"Unhandled exception: {exc}",
                )

            results.append(result)
            self._dispatch_alerts(result)

        pipeline = Pipeline(name="runner", checks=self._checks)
        return PipelineReport(pipeline=pipeline, results=results)

    def _dispatch_alerts(self, result: CheckResult) -> None:
        """Send alerts for non-passing results."""
        for handler in self._alert_handlers:
            try:
                handler.send(result)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Alert handler '%s' raised an error for check '%s'",
                    type(handler).__name__,
                    result.check_name,
                )

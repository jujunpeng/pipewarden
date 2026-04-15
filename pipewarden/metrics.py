"""Metrics collection for pipeline health check runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class CheckMetrics:
    """Aggregated metrics for a single named check."""

    name: str
    total_runs: int = 0
    passed_runs: int = 0
    failed_runs: int = 0
    error_runs: int = 0
    durations_ms: List[float] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Return the fraction of runs that passed (0.0–1.0)."""
        if self.total_runs == 0:
            return 0.0
        return self.passed_runs / self.total_runs

    @property
    def avg_duration_ms(self) -> float:
        """Return the average duration in milliseconds, or 0.0 if no data."""
        if not self.durations_ms:
            return 0.0
        return sum(self.durations_ms) / len(self.durations_ms)


class MetricsCollector:
    """Collects and aggregates metrics across multiple check results."""

    def __init__(self) -> None:
        self._metrics: Dict[str, CheckMetrics] = {}

    def record(self, result: CheckResult) -> None:
        """Record a single CheckResult into the aggregated metrics."""
        name = result.check_name
        if name not in self._metrics:
            self._metrics[name] = CheckMetrics(name=name)

        m = self._metrics[name]
        m.total_runs += 1

        if result.status == CheckStatus.PASSED:
            m.passed_runs += 1
        elif result.status == CheckStatus.FAILED:
            m.failed_runs += 1
        elif result.status == CheckStatus.ERROR:
            m.error_runs += 1

        if result.duration_ms is not None:
            m.durations_ms.append(result.duration_ms)

    def get(self, name: str) -> CheckMetrics:
        """Return metrics for a check by name, raising KeyError if unknown."""
        if name not in self._metrics:
            raise KeyError(f"No metrics recorded for check: {name!r}")
        return self._metrics[name]

    def all_metrics(self) -> Dict[str, CheckMetrics]:
        """Return a copy of all collected metrics keyed by check name."""
        return dict(self._metrics)

    def reset(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()

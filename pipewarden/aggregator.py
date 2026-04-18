"""Aggregates CheckResults across multiple pipeline runs into a summary."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from collections import defaultdict

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class AggregatedSummary:
    check_name: str
    total_runs: int
    pass_count: int
    fail_count: int
    error_count: int

    @property
    def pass_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.pass_count / self.total_runs

    def __repr__(self) -> str:
        return (
            f"AggregatedSummary(check={self.check_name!r}, "
            f"runs={self.total_runs}, pass_rate={self.pass_rate:.2f})"
        )


class ResultAggregator:
    """Collects CheckResults and produces per-check aggregated summaries."""

    def __init__(self) -> None:
        self._buckets: Dict[str, List[CheckResult]] = defaultdict(list)

    def record(self, result: CheckResult) -> None:
        self._buckets[result.check_name].append(result)

    def record_many(self, results: List[CheckResult]) -> None:
        for r in results:
            self.record(r)

    def summary(self, check_name: str) -> AggregatedSummary:
        results = self._buckets.get(check_name, [])
        pass_count = sum(1 for r in results if r.status == CheckStatus.PASSED)
        fail_count = sum(1 for r in results if r.status == CheckStatus.FAILED)
        error_count = sum(1 for r in results if r.status == CheckStatus.ERROR)
        return AggregatedSummary(
            check_name=check_name,
            total_runs=len(results),
            pass_count=pass_count,
            fail_count=fail_count,
            error_count=error_count,
        )

    def all_summaries(self) -> List[AggregatedSummary]:
        return [self.summary(name) for name in self._buckets]

    def check_names(self) -> List[str]:
        return list(self._buckets.keys())

    def reset(self) -> None:
        self._buckets.clear()

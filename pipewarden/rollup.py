"""Rollup: aggregate check results across multiple pipeline reports into a time-bucketed summary."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class RollupBucket:
    """A single time bucket holding aggregated stats."""
    label: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    def __repr__(self) -> str:
        return (
            f"RollupBucket(label={self.label!r}, total={self.total}, "
            f"passed={self.passed}, failed={self.failed}, errors={self.errors})"
        )


class PipelineRollup:
    """Accumulates CheckResults into named buckets for period-over-period reporting."""

    def __init__(self) -> None:
        self._buckets: Dict[str, RollupBucket] = {}
        self._recorded_at: datetime = datetime.now(timezone.utc)

    @property
    def bucket_names(self) -> List[str]:
        return list(self._buckets.keys())

    @property
    def recorded_at(self) -> datetime:
        return self._recorded_at

    def record(self, bucket_label: str, result: CheckResult) -> None:
        if not bucket_label or not bucket_label.strip():
            raise ValueError("bucket_label must be a non-empty string")
        if not isinstance(result, CheckResult):
            raise TypeError("result must be a CheckResult instance")
        if bucket_label not in self._buckets:
            self._buckets[bucket_label] = RollupBucket(label=bucket_label)
        bucket = self._buckets[bucket_label]
        bucket.total += 1
        if result.status == CheckStatus.PASSED:
            bucket.passed += 1
        elif result.status == CheckStatus.FAILED:
            bucket.failed += 1
        else:
            bucket.errors += 1

    def get(self, bucket_label: str) -> RollupBucket:
        if bucket_label not in self._buckets:
            raise KeyError(f"No bucket found for label: {bucket_label!r}")
        return self._buckets[bucket_label]

    def all_buckets(self) -> List[RollupBucket]:
        return list(self._buckets.values())

    def __len__(self) -> int:
        return len(self._buckets)

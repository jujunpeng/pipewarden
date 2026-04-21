"""Check failure heatmap: tracks failure counts per check over time buckets."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class HeatmapCell:
    """A single (check_name, bucket_label) cell in the heatmap."""

    check_name: str
    bucket: str
    failure_count: int
    total_count: int

    @property
    def failure_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.failure_count / self.total_count

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"HeatmapCell(check={self.check_name!r}, bucket={self.bucket!r}, "
            f"failures={self.failure_count}/{self.total_count})"
        )


class CheckHeatmap:
    """Aggregates CheckResult observations into hourly buckets per check."""

    def __init__(self, bucket_format: str = "%Y-%m-%dT%H") -> None:
        if not bucket_format:
            raise ValueError("bucket_format must be a non-empty strftime string")
        self._bucket_format = bucket_format
        # {check_name: {bucket: [total, failures]}}
        self._data: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0]))

    @property
    def bucket_format(self) -> str:
        return self._bucket_format

    def record(self, result: CheckResult) -> None:
        """Record a CheckResult into the appropriate time bucket."""
        ts: datetime = result.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        bucket = ts.strftime(self._bucket_format)
        cell = self._data[result.check_name][bucket]
        cell[0] += 1
        if result.status in (CheckStatus.FAILED, CheckStatus.ERROR):
            cell[1] += 1

    def get(self, check_name: str, bucket: str) -> Optional[HeatmapCell]:
        """Return the HeatmapCell for a specific check and bucket, or None."""
        if check_name not in self._data:
            return None
        if bucket not in self._data[check_name]:
            return None
        total, failures = self._data[check_name][bucket]
        return HeatmapCell(check_name=check_name, bucket=bucket, failure_count=failures, total_count=total)

    def check_names(self) -> List[str]:
        """Return sorted list of all tracked check names."""
        return sorted(self._data.keys())

    def buckets_for(self, check_name: str) -> List[str]:
        """Return sorted list of buckets recorded for a check."""
        return sorted(self._data.get(check_name, {}).keys())

    def hottest(self, top_n: int = 5) -> List[HeatmapCell]:
        """Return the top_n cells with the highest failure counts."""
        cells: List[HeatmapCell] = []
        for check_name, buckets in self._data.items():
            for bucket, (total, failures) in buckets.items():
                cells.append(HeatmapCell(check_name=check_name, bucket=bucket, failure_count=failures, total_count=total))
        cells.sort(key=lambda c: c.failure_count, reverse=True)
        return cells[:top_n]

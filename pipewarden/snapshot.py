"""Pipeline snapshot: captures and compares pipeline state at a point in time."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class PipelineSnapshot:
    """Immutable record of pipeline check results at a specific moment."""

    taken_at: datetime
    results: List[CheckResult]
    label: str = ""

    def passed(self) -> bool:
        return all(r.status == CheckStatus.PASSED for r in self.results)

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s.value: 0 for s in CheckStatus}
        for r in self.results:
            counts[r.status.value] += 1
        return counts

    def find(self, check_name: str) -> Optional[CheckResult]:
        for r in self.results:
            if r.check_name == check_name:
                return r
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PipelineSnapshot(label={self.label!r}, "
            f"taken_at={self.taken_at.isoformat()}, "
            f"results={len(self.results)})"
        )


class SnapshotStore:
    """Stores an ordered history of PipelineSnapshots with a configurable cap."""

    def __init__(self, max_snapshots: int = 50) -> None:
        if max_snapshots < 1:
            raise ValueError("max_snapshots must be at least 1")
        self._max = max_snapshots
        self._snapshots: List[PipelineSnapshot] = []

    @property
    def max_snapshots(self) -> int:
        return self._max

    def save(self, snapshot: PipelineSnapshot) -> None:
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max:
            self._snapshots.pop(0)

    def latest(self) -> Optional[PipelineSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def all(self) -> List[PipelineSnapshot]:
        return list(self._snapshots)

    def diff(self) -> Optional[Dict[str, object]]:
        """Compare the two most recent snapshots; returns None if fewer than two exist."""
        if len(self._snapshots) < 2:
            return None
        prev, curr = self._snapshots[-2], self._snapshots[-1]
        prev_names = {r.check_name: r.status for r in prev.results}
        curr_names = {r.check_name: r.status for r in curr.results}
        changed = {
            name: {"before": prev_names[name].value, "after": curr_names[name].value}
            for name in curr_names
            if name in prev_names and curr_names[name] != prev_names[name]
        }
        added = [n for n in curr_names if n not in prev_names]
        removed = [n for n in prev_names if n not in curr_names]
        return {"changed": changed, "added": added, "removed": removed}

    def __len__(self) -> int:
        return len(self._snapshots)

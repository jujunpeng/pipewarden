"""CheckComparator: compare two PipelineSnapshots and report differences."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewarden.checks import CheckStatus
from pipewarden.snapshot import PipelineSnapshot


@dataclass(frozen=True)
class CheckDiff:
    """Describes how a single check result changed between two snapshots."""

    check_name: str
    previous_status: Optional[CheckStatus]
    current_status: Optional[CheckStatus]

    @property
    def is_regression(self) -> bool:
        """True when a previously passing check is now failing or erroring."""
        return (
            self.previous_status == CheckStatus.PASSED
            and self.current_status in (CheckStatus.FAILED, CheckStatus.ERROR)
        )

    @property
    def is_recovery(self) -> bool:
        """True when a previously failing/erroring check now passes."""
        return (
            self.previous_status in (CheckStatus.FAILED, CheckStatus.ERROR)
            and self.current_status == CheckStatus.PASSED
        )

    @property
    def is_new(self) -> bool:
        """True when the check did not exist in the previous snapshot."""
        return self.previous_status is None

    @property
    def is_removed(self) -> bool:
        """True when the check no longer exists in the current snapshot."""
        return self.current_status is None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CheckDiff(name={self.check_name!r}, "
            f"{self.previous_status} -> {self.current_status})"
        )


@dataclass
class SnapshotComparison:
    """Aggregated result of comparing two snapshots."""

    diffs: List[CheckDiff] = field(default_factory=list)

    @property
    def regressions(self) -> List[CheckDiff]:
        return [d for d in self.diffs if d.is_regression]

    @property
    def recoveries(self) -> List[CheckDiff]:
        return [d for d in self.diffs if d.is_recovery]

    @property
    def new_checks(self) -> List[CheckDiff]:
        return [d for d in self.diffs if d.is_new]

    @property
    def removed_checks(self) -> List[CheckDiff]:
        return [d for d in self.diffs if d.is_removed]

    @property
    def has_regressions(self) -> bool:
        return bool(self.regressions)

    def summary(self) -> str:
        """Return a human-readable one-line summary of the comparison."""
        parts = []
        if self.regressions:
            parts.append(f"{len(self.regressions)} regression(s)")
        if self.recoveries:
            parts.append(f"{len(self.recoveries)} recovery(s)")
        if self.new_checks:
            parts.append(f"{len(self.new_checks)} new check(s)")
        if self.removed_checks:
            parts.append(f"{len(self.removed_checks)} removed check(s)")
        return ", ".join(parts) if parts else "no changes"


class CheckComparator:
    """Compare two PipelineSnapshots and produce a SnapshotComparison."""

    def compare(
        self,
        previous: PipelineSnapshot,
        current: PipelineSnapshot,
    ) -> SnapshotComparison:
        prev_map = {r.check_name: r.status for r in previous.results}
        curr_map = {r.check_name: r.status for r in current.results}

        all_names = set(prev_map) | set(curr_map)
        diffs: List[CheckDiff] = []

        for name in sorted(all_names):
            prev_status = prev_map.get(name)
            curr_status = curr_map.get(name)
            if prev_status != curr_status:
                diffs.append(
                    CheckDiff(
                        check_name=name,
                        previous_status=prev_status,
                        current_status=curr_status,
                    )
                )

        return SnapshotComparison(diffs=diffs)

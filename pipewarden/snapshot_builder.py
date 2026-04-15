"""Utility for building PipelineSnapshots from runner output."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pipewarden.pipeline import PipelineReport
from pipewarden.snapshot import PipelineSnapshot, SnapshotStore


class SnapshotBuilder:
    """Creates PipelineSnapshot objects from PipelineReport instances and
    optionally persists them to a SnapshotStore."""

    def __init__(self, store: Optional[SnapshotStore] = None) -> None:
        self._store = store

    @property
    def store(self) -> Optional[SnapshotStore]:
        return self._store

    def build(
        self,
        report: PipelineReport,
        label: str = "",
        taken_at: Optional[datetime] = None,
    ) -> PipelineSnapshot:
        """Build a snapshot from a PipelineReport.

        Args:
            report: The pipeline report to snapshot.
            label: Optional human-readable label for the snapshot.
            taken_at: Timestamp for the snapshot; defaults to now (UTC).

        Returns:
            A new PipelineSnapshot.
        """
        if taken_at is None:
            taken_at = datetime.now(timezone.utc)

        snapshot = PipelineSnapshot(
            taken_at=taken_at,
            results=list(report.results),
            label=label,
        )

        if self._store is not None:
            self._store.save(snapshot)

        return snapshot

    def latest(self) -> Optional[PipelineSnapshot]:
        """Return the latest snapshot from the store, or None."""
        if self._store is None:
            return None
        return self._store.latest()

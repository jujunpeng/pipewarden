"""Periodic digest reporting for pipeline health summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewarden.snapshot import PipelineSnapshot


@dataclass
class DigestEntry:
    """A single snapshot entry included in a digest."""

    snapshot: PipelineSnapshot
    recorded_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DigestEntry(recorded_at={self.recorded_at.isoformat()}, "
            f"passed={self.snapshot.passed})"
        )


class PipelineDigest:
    """Accumulates snapshots and renders a periodic health digest."""

    def __init__(self, title: str = "Pipeline Digest") -> None:
        if not title or not title.strip():
            raise ValueError("title must be a non-empty string")
        self._title = title
        self._entries: List[DigestEntry] = []

    @property
    def title(self) -> str:
        return self._title

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def add(self, snapshot: PipelineSnapshot) -> None:
        """Record a snapshot into the digest."""
        self._entries.append(DigestEntry(snapshot=snapshot))

    def clear(self) -> None:
        """Remove all accumulated entries."""
        self._entries.clear()

    def overall_pass_rate(self) -> float:
        """Return the fraction of snapshots that fully passed."""
        if not self._entries:
            return 0.0
        passed = sum(1 for e in self._entries if e.snapshot.passed)
        return passed / len(self._entries)

    def render(self) -> str:
        """Render a human-readable digest summary."""
        lines: List[str] = [
            f"=== {self._title} ===",
            f"Snapshots : {self.entry_count}",
            f"Pass rate : {self.overall_pass_rate():.0%}",
        ]
        for idx, entry in enumerate(self._entries, start=1):
            status = "PASS" if entry.snapshot.passed else "FAIL"
            lines.append(
                f"  [{idx:02d}] {entry.recorded_at.strftime('%Y-%m-%dT%H:%M:%S')} "
                f"{status} — {entry.snapshot.summary}"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"PipelineDigest(title={self._title!r}, entries={self.entry_count})"

"""Report utilities for a ResultSampler snapshot."""
from __future__ import annotations

from typing import Dict

from pipewarden.checks import CheckStatus
from pipewarden.sampler import ResultSampler


class SampleReport:
    """Summarises the contents of a :class:`ResultSampler` reservoir."""

    def __init__(self, sampler: ResultSampler) -> None:
        self._sampler = sampler

    @property
    def sample_count(self) -> int:
        return len(self._sampler)

    @property
    def total_seen(self) -> int:
        return self._sampler.total_seen

    def status_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s.value: 0 for s in CheckStatus}
        for result in self._sampler.samples():
            counts[result.status.value] += 1
        return counts

    def pass_rate(self) -> float:
        samples = self._sampler.samples()
        if not samples:
            return 0.0
        passed = sum(1 for r in samples if r.status == CheckStatus.PASSED)
        return passed / len(samples)

    def render(self) -> str:
        counts = self.status_counts()
        lines = [
            f"Sample Report ({self.sample_count} samples / {self.total_seen} total seen)",
            f"  Pass rate : {self.pass_rate():.1%}",
        ]
        for status, count in counts.items():
            lines.append(f"  {status:<8}: {count}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return (
            f"SampleReport(sample_count={self.sample_count}, "
            f"total_seen={self.total_seen})"
        )

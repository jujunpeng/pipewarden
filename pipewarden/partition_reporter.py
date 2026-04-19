"""Render a summary report for a ResultPartitioner."""
from __future__ import annotations
from pipewarden.partition import ResultPartitioner
from pipewarden.checks import CheckStatus


class PartitionReport:
    """Generates a human-readable summary of partitioned results."""

    def __init__(self, partitioner: ResultPartitioner) -> None:
        if not isinstance(partitioner, ResultPartitioner):
            raise TypeError("partitioner must be a ResultPartitioner instance.")
        self._partitioner = partitioner

    def render(self) -> str:
        lines = ["=== Partition Report ==="]
        for name in self._partitioner.partition_names():
            partition = self._partitioner.get(name)
            results = partition.results()
            total = len(results)
            passed = sum(1 for r in results if r.status == CheckStatus.PASSED)
            failed = sum(1 for r in results if r.status == CheckStatus.FAILED)
            errors = sum(1 for r in results if r.status == CheckStatus.ERROR)
            lines.append(
                f"  [{name}] total={total} passed={passed} failed={failed} errors={errors}"
            )
        unmatched = self._partitioner.unmatched()
        lines.append(f"  [unmatched] total={len(unmatched)}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()

"""Filtering utilities for CheckResult collections."""

from typing import List, Optional, Sequence
from pipewarden.checks import CheckResult, CheckStatus


class CheckFilter:
    """Provides filtering operations over a sequence of CheckResults."""

    def __init__(self, results: Sequence[CheckResult]) -> None:
        self._results = list(results)

    @property
    def results(self) -> List[CheckResult]:
        """Return the full list of results held by this filter."""
        return list(self._results)

    def by_status(self, status: CheckStatus) -> List[CheckResult]:
        """Return only results matching the given status."""
        return [r for r in self._results if r.status == status]

    def passed(self) -> List[CheckResult]:
        """Return results with PASSED status."""
        return self.by_status(CheckStatus.PASSED)

    def failed(self) -> List[CheckResult]:
        """Return results with FAILED status."""
        return self.by_status(CheckStatus.FAILED)

    def errored(self) -> List[CheckResult]:
        """Return results with ERROR status."""
        return self.by_status(CheckStatus.ERROR)

    def by_check_name(self, name: str) -> List[CheckResult]:
        """Return results whose check_name matches *name* exactly."""
        return [r for r in self._results if r.check_name == name]

    def with_message_containing(self, substring: str) -> List[CheckResult]:
        """Return results whose message contains *substring* (case-insensitive)."""
        lower = substring.lower()
        return [
            r for r in self._results
            if r.message is not None and lower in r.message.lower()
        ]

    def above_duration_ms(self, threshold_ms: float) -> List[CheckResult]:
        """Return results whose duration_ms exceeds *threshold_ms*."""
        return [
            r for r in self._results
            if r.duration_ms is not None and r.duration_ms > threshold_ms
        ]

    def __len__(self) -> int:
        return len(self._results)

    def __repr__(self) -> str:  # pragma: no cover
        return f"CheckFilter(results={len(self._results)})"

"""Check result history tracking for pipewarden."""

from collections import deque
from typing import Deque, Dict, List, Optional

from pipewarden.checks import CheckResult, CheckStatus


class CheckHistory:
    """Stores a rolling history of CheckResult objects per check name."""

    def __init__(self, max_size: int = 100) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._max_size = max_size
        self._records: Dict[str, Deque[CheckResult]] = {}

    @property
    def max_size(self) -> int:
        return self._max_size

    def record(self, result: CheckResult) -> None:
        """Append a CheckResult to the history for its check name."""
        name = result.check_name
        if name not in self._records:
            self._records[name] = deque(maxlen=self._max_size)
        self._records[name].append(result)

    def get(self, check_name: str) -> List[CheckResult]:
        """Return all recorded results for a given check name."""
        return list(self._records.get(check_name, []))

    def latest(self, check_name: str) -> Optional[CheckResult]:
        """Return the most recent result for a given check name, or None."""
        records = self._records.get(check_name)
        if not records:
            return None
        return records[-1]

    def known_checks(self) -> List[str]:
        """Return a sorted list of all check names that have been recorded."""
        return sorted(self._records.keys())

    def failure_rate(self, check_name: str) -> float:
        """Return the fraction of non-passing results for a check (0.0–1.0)."""
        records = self._records.get(check_name)
        if not records:
            return 0.0
        non_passing = sum(
            1 for r in records if r.status != CheckStatus.PASSED
        )
        return non_passing / len(records)

    def clear(self, check_name: Optional[str] = None) -> None:
        """Clear history for a specific check or all checks if name is None."""
        if check_name is None:
            self._records.clear()
        else:
            self._records.pop(check_name, None)

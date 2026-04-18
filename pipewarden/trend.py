from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class TrendWindow:
    """Sliding window of recent results for a single check."""
    check_name: str
    max_size: int = 10
    _results: List[CheckResult] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if self.max_size < 1:
            raise ValueError("max_size must be at least 1")

    def record(self, result: CheckResult) -> None:
        if result.check_name != self.check_name:
            raise ValueError(
                f"Expected check '{self.check_name}', got '{result.check_name}'"
            )
        self._results.append(result)
        if len(self._results) > self.max_size:
            self._results.pop(0)

    @property
    def results(self) -> List[CheckResult]:
        return list(self._results)

    @property
    def size(self) -> int:
        return len(self._results)

    @property
    def pass_rate(self) -> float:
        if not self._results:
            return 0.0
        passed = sum(1 for r in self._results if r.status == CheckStatus.PASSED)
        return passed / len(self._results)

    @property
    def is_degrading(self) -> bool:
        """True if the last result failed and pass_rate dropped below 0.5."""
        if not self._results:
            return False
        last = self._results[-1]
        return last.status != CheckStatus.PASSED and self.pass_rate < 0.5

    @property
    def is_recovering(self) -> bool:
        """True if the last result passed and pass_rate was previously below 0.5."""
        if len(self._results) < 2:
            return False
        last = self._results[-1]
        prior_rate = sum(
            1 for r in self._results[:-1] if r.status == CheckStatus.PASSED
        ) / (len(self._results) - 1)
        return last.status == CheckStatus.PASSED and prior_rate < 0.5

    def __repr__(self) -> str:
        return (
            f"TrendWindow(check_name={self.check_name!r}, "
            f"size={self.size}, pass_rate={self.pass_rate:.2f})"
        )


class TrendTracker:
    """Tracks TrendWindows for multiple checks."""

    def __init__(self, max_size: int = 10) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._max_size = max_size
        self._windows: dict[str, TrendWindow] = {}

    @property
    def max_size(self) -> int:
        return self._max_size

    def record(self, result: CheckResult) -> None:
        name = result.check_name
        if name not in self._windows:
            self._windows[name] = TrendWindow(name, self._max_size)
        self._windows[name].record(result)

    def get(self, check_name: str) -> Optional[TrendWindow]:
        return self._windows.get(check_name)

    @property
    def tracked_checks(self) -> List[str]:
        return list(self._windows.keys())

    def degrading_checks(self) -> List[str]:
        return [n for n, w in self._windows.items() if w.is_degrading]

    def recovering_checks(self) -> List[str]:
        return [n for n, w in self._windows.items() if w.is_recovering]

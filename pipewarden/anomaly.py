from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class AnomalyAlert:
    check_name: str
    reason: str
    result: CheckResult

    def __repr__(self) -> str:
        return f"AnomalyAlert(check={self.check_name!r}, reason={self.reason!r})"


@dataclass
class AnomalyDetector:
    check_name: str
    window_size: int = 10
    failure_rate_threshold: float = 0.5
    _history: List[CheckResult] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.window_size < 1:
            raise ValueError("window_size must be at least 1")
        if not (0.0 < self.failure_rate_threshold <= 1.0):
            raise ValueError("failure_rate_threshold must be in (0, 1]")

    def observe(self, result: CheckResult) -> Optional[AnomalyAlert]:
        if result.check_name != self.check_name:
            raise ValueError(
                f"Expected check {self.check_name!r}, got {result.check_name!r}"
            )
        self._history.append(result)
        if len(self._history) > self.window_size:
            self._history = self._history[-self.window_size :]
        return self._evaluate(result)

    def _evaluate(self, result: CheckResult) -> Optional[AnomalyAlert]:
        if len(self._history) < self.window_size:
            return None
        failures = sum(
            1 for r in self._history if r.status != CheckStatus.PASSED
        )
        rate = failures / len(self._history)
        if rate >= self.failure_rate_threshold:
            return AnomalyAlert(
                check_name=self.check_name,
                reason=f"failure rate {rate:.0%} >= threshold {self.failure_rate_threshold:.0%}",
                result=result,
            )
        return None

    @property
    def history_size(self) -> int:
        return len(self._history)

    def reset(self) -> None:
        self._history.clear()

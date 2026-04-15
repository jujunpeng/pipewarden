"""Baseline tracking for check durations and pass rates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class BaselineStats:
    """Stores baseline statistics for a single check."""

    check_name: str
    expected_pass_rate: float  # 0.0 – 1.0
    expected_max_duration_ms: Optional[float] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.expected_pass_rate <= 1.0):
            raise ValueError(
                f"expected_pass_rate must be between 0.0 and 1.0, got {self.expected_pass_rate}"
            )
        if self.expected_max_duration_ms is not None and self.expected_max_duration_ms <= 0:
            raise ValueError(
                f"expected_max_duration_ms must be positive, got {self.expected_max_duration_ms}"
            )


@dataclass
class BaselineViolation:
    """Describes a single baseline violation for a check result."""

    check_name: str
    reason: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"BaselineViolation(check={self.check_name!r}, reason={self.reason!r})"


class BaselineMonitor:
    """Compares CheckResults against registered baselines."""

    def __init__(self) -> None:
        self._baselines: Dict[str, BaselineStats] = {}

    def register(self, stats: BaselineStats) -> None:
        """Register or replace a baseline for a check."""
        self._baselines[stats.check_name] = stats

    def get(self, check_name: str) -> Optional[BaselineStats]:
        """Return the baseline for *check_name*, or None."""
        return self._baselines.get(check_name)

    def evaluate(self, result: CheckResult) -> Optional[BaselineViolation]:
        """Return a BaselineViolation if *result* breaches its baseline, else None."""
        baseline = self._baselines.get(result.check_name)
        if baseline is None:
            return None

        # Duration check
        if (
            baseline.expected_max_duration_ms is not None
            and result.duration_ms is not None
            and result.duration_ms > baseline.expected_max_duration_ms
        ):
            return BaselineViolation(
                check_name=result.check_name,
                reason=(
                    f"duration {result.duration_ms:.1f} ms exceeds baseline "
                    f"{baseline.expected_max_duration_ms:.1f} ms"
                ),
            )

        # Status check — treat anything other than PASSED as a failure signal
        if result.status != CheckStatus.PASSED:
            pass_rate_implied = 0.0
            if pass_rate_implied < baseline.expected_pass_rate:
                return BaselineViolation(
                    check_name=result.check_name,
                    reason=(
                        f"check did not pass (status={result.status.value}); "
                        f"expected pass rate >= {baseline.expected_pass_rate}"
                    ),
                )

        return None

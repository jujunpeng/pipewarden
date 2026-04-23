"""Failure rate forecasting based on recent trend windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class ForecastPoint:
    """A single predicted failure-rate data point."""

    step: int          # steps ahead (1-based)
    failure_rate: float  # predicted failure rate in [0.0, 1.0]

    def __repr__(self) -> str:
        return f"ForecastPoint(step={self.step}, failure_rate={self.failure_rate:.3f})"


@dataclass
class CheckForecaster:
    """Forecasts future failure rates for a single check using a simple
    exponential-smoothing model over observed failure rates.

    Args:
        check_name: Name of the check being tracked.
        alpha:      Smoothing factor in (0, 1].  Higher values weight recent
                    observations more heavily.
        horizon:    Number of future steps to forecast.
    """

    check_name: str
    alpha: float = 0.3
    horizon: int = 3

    _smoothed: Optional[float] = field(default=None, init=False, repr=False)
    _total: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not (0.0 < self.alpha <= 1.0):
            raise ValueError("alpha must be in (0, 1]")
        if self.horizon < 1:
            raise ValueError("horizon must be >= 1")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def observe(self, result: CheckResult) -> None:
        """Feed a new CheckResult into the model."""
        if result.check_name != self.check_name:
            raise ValueError(
                f"Expected result for '{self.check_name}', "
                f"got '{result.check_name}'"
            )
        failed = 1.0 if result.status != CheckStatus.PASSED else 0.0
        if self._smoothed is None:
            self._smoothed = failed
        else:
            self._smoothed = self.alpha * failed + (1.0 - self.alpha) * self._smoothed
        self._total += 1

    def forecast(self) -> List[ForecastPoint]:
        """Return *horizon* forecast points.

        If no observations have been made the forecast is all-zero.
        """
        base = self._smoothed if self._smoothed is not None else 0.0
        return [
            ForecastPoint(step=i + 1, failure_rate=round(base, 6))
            for i in range(self.horizon)
        ]

    @property
    def smoothed_failure_rate(self) -> Optional[float]:
        """Current smoothed failure rate, or None if no data yet."""
        return self._smoothed

    @property
    def total_observed(self) -> int:
        return self._total

    def reset(self) -> None:
        self._smoothed = None
        self._total = 0

"""Drift detection for pipeline health checks.

Tracks how check results deviate from a stable baseline over time,
raising alerts when the observed pass rate drifts beyond a configurable
tolerance band.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class DriftAlert:
    """Emitted when a check's pass rate drifts beyond the allowed tolerance."""

    check_name: str
    baseline_pass_rate: float
    observed_pass_rate: float
    tolerance: float

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DriftAlert(check={self.check_name!r}, "
            f"baseline={self.baseline_pass_rate:.2f}, "
            f"observed={self.observed_pass_rate:.2f}, "
            f"tolerance={self.tolerance:.2f})"
        )


class DriftDetector:
    """Detects pass-rate drift for a single check relative to a fixed baseline.

    Parameters
    ----------
    check_name:
        The name of the check being monitored.
    baseline_pass_rate:
        Expected pass rate in the range [0.0, 1.0].
    tolerance:
        Maximum allowed absolute deviation from the baseline before an alert
        is raised (e.g. 0.1 means ±10 percentage points).
    window_size:
        Number of recent results used to compute the observed pass rate.
    """

    def __init__(
        self,
        check_name: str,
        baseline_pass_rate: float,
        tolerance: float = 0.1,
        window_size: int = 20,
    ) -> None:
        if not (0.0 <= baseline_pass_rate <= 1.0):
            raise ValueError("baseline_pass_rate must be in [0.0, 1.0]")
        if not (0.0 < tolerance <= 1.0):
            raise ValueError("tolerance must be in (0.0, 1.0]")
        if window_size < 1:
            raise ValueError("window_size must be at least 1")

        self._check_name = check_name
        self._baseline = baseline_pass_rate
        self._tolerance = tolerance
        self._window: deque[CheckResult] = deque(maxlen=window_size)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def check_name(self) -> str:
        return self._check_name

    @property
    def baseline_pass_rate(self) -> float:
        return self._baseline

    @property
    def tolerance(self) -> float:
        return self._tolerance

    @property
    def window_size(self) -> int:
        return self._window.maxlen  # type: ignore[return-value]

    @property
    def observed_pass_rate(self) -> Optional[float]:
        """Current pass rate computed from the observation window.

        Returns ``None`` when the window is empty.
        """
        if not self._window:
            return None
        passed = sum(1 for r in self._window if r.status == CheckStatus.PASSED)
        return passed / len(self._window)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def observe(self, result: CheckResult) -> Optional[DriftAlert]:
        """Record a new result and return a :class:`DriftAlert` if drift is detected.

        Parameters
        ----------
        result:
            A :class:`~pipewarden.checks.CheckResult` whose ``check_name``
            must match this detector's ``check_name``.

        Returns
        -------
        DriftAlert or None
            An alert when the observed pass rate deviates from the baseline
            by more than *tolerance*; otherwise ``None``.
        """
        if result.check_name != self._check_name:
            raise ValueError(
                f"Expected result for {self._check_name!r}, "
                f"got {result.check_name!r}"
            )

        self._window.append(result)
        rate = self.observed_pass_rate
        if rate is None:
            return None

        if abs(rate - self._baseline) > self._tolerance:
            return DriftAlert(
                check_name=self._check_name,
                baseline_pass_rate=self._baseline,
                observed_pass_rate=rate,
                tolerance=self._tolerance,
            )
        return None

    def reset(self) -> None:
        """Clear all observations from the window."""
        self._window.clear()


class DriftMonitor:
    """Manages :class:`DriftDetector` instances for multiple checks and
    dispatches :class:`DriftAlert` objects to registered handlers.

    Parameters
    ----------
    handlers:
        Zero or more callables that accept a :class:`DriftAlert`.
    """

    def __init__(self, handlers: Optional[Sequence[Callable[[DriftAlert], None]]] = None) -> None:
        self._detectors: dict[str, DriftDetector] = {}
        self._handlers: List[Callable[[DriftAlert], None]] = list(handlers or [])

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add_detector(self, detector: DriftDetector) -> None:
        """Register a detector.  Raises :class:`ValueError` on duplicate names."""
        if detector.check_name in self._detectors:
            raise ValueError(f"Detector for {detector.check_name!r} already registered")
        self._detectors[detector.check_name] = detector

    def add_handler(self, handler: Callable[[DriftAlert], None]) -> None:
        """Add an alert handler callable."""
        self._handlers.append(handler)

    @property
    def check_names(self) -> List[str]:
        return list(self._detectors)

    # ------------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------------

    def observe(self, result: CheckResult) -> Optional[DriftAlert]:
        """Route *result* to the matching detector (if any) and fire handlers.

        Unknown check names are silently ignored so the monitor can be used
        alongside checks that are not under drift surveillance.

        Returns
        -------
        DriftAlert or None
            The alert that was dispatched, or ``None``.
        """
        detector = self._detectors.get(result.check_name)
        if detector is None:
            return None

        alert = detector.observe(result)
        if alert is not None:
            for handler in self._handlers:
                handler(alert)
        return alert

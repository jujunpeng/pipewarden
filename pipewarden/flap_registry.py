"""Registry that manages one FlapDetector per check name."""

from __future__ import annotations

from typing import Dict, List

from pipewarden.checks import CheckResult
from pipewarden.flap_detector import FlapAlert, FlapDetector


class FlapRegistry:
    """Maintains a FlapDetector for every check seen and dispatches alerts."""

    def __init__(
        self,
        default_window_size: int = 10,
        default_threshold: int = 4,
    ) -> None:
        if default_window_size < 2:
            raise ValueError("default_window_size must be at least 2")
        if default_threshold < 1:
            raise ValueError("default_threshold must be at least 1")
        if default_threshold >= default_window_size:
            raise ValueError("default_threshold must be less than default_window_size")

        self._default_window_size = default_window_size
        self._default_threshold = default_threshold
        self._detectors: Dict[str, FlapDetector] = {}

    @property
    def default_window_size(self) -> int:
        return self._default_window_size

    @property
    def default_threshold(self) -> int:
        return self._default_threshold

    @property
    def check_names(self) -> List[str]:
        return list(self._detectors.keys())

    def observe(self, result: CheckResult) -> FlapAlert | None:
        """Record *result* in the appropriate detector and return any alert."""
        detector = self._get_or_create(result.check_name)
        return detector.observe(result)

    def get(self, check_name: str) -> FlapDetector | None:
        """Return the detector for *check_name*, or None if not yet seen."""
        return self._detectors.get(check_name)

    def reset(self, check_name: str) -> None:
        """Reset the detector window for *check_name* if it exists."""
        detector = self._detectors.get(check_name)
        if detector is not None:
            detector.reset()

    def reset_all(self) -> None:
        """Reset all detector windows."""
        for detector in self._detectors.values():
            detector.reset()

    def _get_or_create(self, check_name: str) -> FlapDetector:
        if check_name not in self._detectors:
            self._detectors[check_name] = FlapDetector(
                check_name=check_name,
                window_size=self._default_window_size,
                threshold=self._default_threshold,
            )
        return self._detectors[check_name]

    def __repr__(self) -> str:
        return (
            f"FlapRegistry(checks={len(self._detectors)}, "
            f"window={self._default_window_size}, threshold={self._default_threshold})"
        )

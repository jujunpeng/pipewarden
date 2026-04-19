from __future__ import annotations
from typing import Dict, List, Optional
from pipewarden.anomaly import AnomalyDetector, AnomalyAlert
from pipewarden.checks import CheckResult


class AnomalyRegistry:
    def __init__(
        self,
        default_window_size: int = 10,
        default_failure_rate_threshold: float = 0.5,
    ) -> None:
        if default_window_size < 1:
            raise ValueError("default_window_size must be at least 1")
        if not (0.0 < default_failure_rate_threshold <= 1.0):
            raise ValueError("default_failure_rate_threshold must be in (0, 1]")
        self._default_window_size = default_window_size
        self._default_threshold = default_failure_rate_threshold
        self._detectors: Dict[str, AnomalyDetector] = {}

    @property
    def default_window_size(self) -> int:
        return self._default_window_size

    @property
    def default_failure_rate_threshold(self) -> float:
        return self._default_threshold

    def _get_or_create(self, check_name: str) -> AnomalyDetector:
        if check_name not in self._detectors:
            self._detectors[check_name] = AnomalyDetector(
                check_name=check_name,
                window_size=self._default_window_size,
                failure_rate_threshold=self._default_threshold,
            )
        return self._detectors[check_name]

    def observe(self, result: CheckResult) -> Optional[AnomalyAlert]:
        detector = self._get_or_create(result.check_name)
        return detector.observe(result)

    def observe_many(self, results: List[CheckResult]) -> List[AnomalyAlert]:
        alerts = []
        for r in results:
            alert = self.observe(r)
            if alert is not None:
                alerts.append(alert)
        return alerts

    def reset(self, check_name: str) -> None:
        if check_name in self._detectors:
            self._detectors[check_name].reset()

    def reset_all(self) -> None:
        for d in self._detectors.values():
            d.reset()

    @property
    def tracked_checks(self) -> List[str]:
        return list(self._detectors.keys())

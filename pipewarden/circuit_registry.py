from __future__ import annotations
from typing import Dict, Optional

from pipewarden.circuit_breaker import CircuitBreaker
from pipewarden.checks import CheckResult


class CircuitRegistry:
    def __init__(
        self,
        default_failure_threshold: int = 3,
        default_recovery_timeout_seconds: float = 60.0,
    ) -> None:
        if default_failure_threshold < 1:
            raise ValueError("default_failure_threshold must be >= 1")
        if default_recovery_timeout_seconds <= 0:
            raise ValueError("default_recovery_timeout_seconds must be > 0")
        self._default_threshold = default_failure_threshold
        self._default_timeout = default_recovery_timeout_seconds
        self._breakers: Dict[str, CircuitBreaker] = {}

    @property
    def default_failure_threshold(self) -> int:
        return self._default_threshold

    @property
    def default_recovery_timeout_seconds(self) -> float:
        return self._default_timeout

    def get(self, check_name: str) -> CircuitBreaker:
        if check_name not in self._breakers:
            self._breakers[check_name] = CircuitBreaker(
                check_name=check_name,
                failure_threshold=self._default_threshold,
                recovery_timeout_seconds=self._default_timeout,
            )
        return self._breakers[check_name]

    def observe(self, result: CheckResult) -> None:
        self.get(result.check_name).observe(result)

    def is_open(self, check_name: str) -> bool:
        return self.get(check_name).is_open()

    def open_circuits(self) -> list[str]:
        return [name for name, cb in self._breakers.items() if cb.is_open()]

    def reset(self, check_name: str) -> None:
        self.get(check_name).reset()

    def __len__(self) -> int:
        return len(self._breakers)

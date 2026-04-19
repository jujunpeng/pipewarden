from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time

from pipewarden.checks import CheckResult, CheckStatus


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    check_name: str
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 60.0
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _failure_count: int = field(default=0, init=False, repr=False)
    _opened_at: Optional[float] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.recovery_timeout_seconds <= 0:
            raise ValueError("recovery_timeout_seconds must be > 0")

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self.recovery_timeout_seconds:
                self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def observe(self, result: CheckResult) -> None:
        if result.check_name != self.check_name:
            raise ValueError(f"Expected check '{self.check_name}', got '{result.check_name}'")
        if result.status == CheckStatus.PASSED:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None
        else:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(check_name={self.check_name!r}, "
            f"state={self.state.value}, failures={self._failure_count})"
        )

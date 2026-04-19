from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Callable

from pipewarden.circuit_breaker import CircuitBreaker, CircuitState
from pipewarden.checks import CheckResult


@dataclass
class CircuitOpenAlert:
    check_name: str
    failure_count: int

    def __repr__(self) -> str:
        return f"CircuitOpenAlert(check_name={self.check_name!r}, failures={self.failure_count})"


AlertCallback = Callable[[CircuitOpenAlert], None]


class CircuitAlertHandler:
    """Wraps a CircuitBreaker and fires callbacks when the circuit opens."""

    def __init__(self, breaker: CircuitBreaker) -> None:
        if not isinstance(breaker, CircuitBreaker):
            raise TypeError("breaker must be a CircuitBreaker instance")
        self._breaker = breaker
        self._handlers: List[AlertCallback] = []
        self._last_state = breaker.state

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def add_handler(self, callback: AlertCallback) -> None:
        self._handlers.append(callback)

    def observe(self, result: CheckResult) -> None:
        self._breaker.observe(result)
        current = self._breaker.state
        if current == CircuitState.OPEN and self._last_state != CircuitState.OPEN:
            alert = CircuitOpenAlert(
                check_name=self._breaker.check_name,
                failure_count=self._breaker.failure_count,
            )
            for handler in self._handlers:
                handler(alert)
        self._last_state = current

    def __repr__(self) -> str:
        return (
            f"CircuitAlertHandler(check_name={self._breaker.check_name!r}, "
            f"handlers={self.handler_count})"
        )

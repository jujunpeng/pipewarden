"""Alert handler for timeout violations."""
from __future__ import annotations

from typing import Callable, List

from pipewarden.alerts import AlertHandler
from pipewarden.checks import CheckResult
from pipewarden.timeout import TimeoutMonitor, TimeoutViolation


class TimeoutBreachAlert:
    """Emitted when a check result exceeds a configured timeout limit."""

    def __init__(self, violation: TimeoutViolation, result: CheckResult) -> None:
        self.violation = violation
        self.result = result

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TimeoutBreachAlert(check_name={self.violation.check_name!r}, "
            f"duration_ms={self.violation.duration_ms:.1f}, "
            f"limit_ms={self.violation.limit_ms:.1f})"
        )


class TimeoutAlertHandler:
    """Checks results against a TimeoutMonitor and dispatches alerts."""

    def __init__(self, monitor: TimeoutMonitor) -> None:
        if not isinstance(monitor, TimeoutMonitor):
            raise TypeError("monitor must be a TimeoutMonitor instance")
        self._monitor = monitor
        self._handlers: List[AlertHandler] = []

    def add_handler(self, handler: AlertHandler) -> None:
        if not isinstance(handler, AlertHandler):
            raise TypeError("handler must be an AlertHandler instance")
        self._handlers.append(handler)

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def observe(self, result: CheckResult) -> list[TimeoutBreachAlert]:
        """Evaluate result; fire alert handlers for each violation found."""
        violations = self._monitor.evaluate(result)
        alerts: list[TimeoutBreachAlert] = []
        for violation in violations:
            alert = TimeoutBreachAlert(violation=violation, result=result)
            alerts.append(alert)
            for handler in self._handlers:
                handler.send(result)
        return alerts

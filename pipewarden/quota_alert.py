"""Alert integration for quota violations."""
from __future__ import annotations

from typing import List

from pipewarden.alerts import AlertHandler
from pipewarden.quota import QuotaViolation


class QuotaExceededAlert:
    """Payload sent to handlers when a check exceeds its run quota."""

    def __init__(self, violation: QuotaViolation) -> None:
        self._violation = violation

    @property
    def violation(self) -> QuotaViolation:
        return self._violation

    def __repr__(self) -> str:
        return f"QuotaExceededAlert(violation={self._violation!r})"


class QuotaAlertHandler:
    """Dispatches QuotaExceededAlert to one or more AlertHandler instances."""

    def __init__(self) -> None:
        self._handlers: List[AlertHandler] = []

    def add_handler(self, handler: AlertHandler) -> None:
        if not isinstance(handler, AlertHandler):
            raise TypeError("handler must be an AlertHandler instance")
        self._handlers.append(handler)

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def notify(self, violation: QuotaViolation) -> None:
        """Build an alert and dispatch it to all registered handlers."""
        alert = QuotaExceededAlert(violation)
        for handler in self._handlers:
            handler.send(alert)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        return f"QuotaAlertHandler(handlers={self.handler_count})"

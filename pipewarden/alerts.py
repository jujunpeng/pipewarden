"""Alerting hooks for pipeline health check notifications."""

from abc import ABC, abstractmethod
from typing import Callable, List
from pipewarden.checks import CheckResult, CheckStatus


class AlertHandler(ABC):
    """Abstract base class for alert handlers."""

    @abstractmethod
    def send(self, result: CheckResult) -> None:
        """Send an alert for the given check result."""
        raise NotImplementedError


class LogAlertHandler(AlertHandler):
    """Alert handler that logs failures to stdout."""

    def __init__(self, prefix: str = "[ALERT]"):
        self.prefix = prefix

    def send(self, result: CheckResult) -> None:
        if result.status != CheckStatus.PASSED:
            print(
                f"{self.prefix} Check '{result.name}' {result.status.value}: "
                f"{result.message} (at {result.timestamp})"
            )


class CallbackAlertHandler(AlertHandler):
    """Alert handler that invokes a user-supplied callable."""

    def __init__(self, callback: Callable[[CheckResult], None]):
        if not callable(callback):
            raise TypeError("callback must be callable")
        self.callback = callback

    def send(self, result: CheckResult) -> None:
        if result.status != CheckStatus.PASSED:
            self.callback(result)


class AlertDispatcher:
    """Dispatches alerts to one or more registered handlers."""

    def __init__(self):
        self._handlers: List[AlertHandler] = []

    def register(self, handler: AlertHandler) -> None:
        """Register an alert handler."""
        if not isinstance(handler, AlertHandler):
            raise TypeError("handler must be an instance of AlertHandler")
        self._handlers.append(handler)

    def dispatch(self, result: CheckResult) -> None:
        """Dispatch a check result to all registered handlers."""
        for handler in self._handlers:
            handler.send(result)

    @property
    def handler_count(self) -> int:
        """Return the number of registered handlers."""
        return len(self._handlers)

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List

from pipewarden.alerts import AlertHandler
from pipewarden.checks import CheckResult
from pipewarden.sla import SLAMonitor, SLAViolation


@dataclass
class SLABreachAlert:
    violation: SLAViolation
    triggered_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"SLABreachAlert(check={self.violation.check_name!r}, "
            f"required={self.violation.required_pass_rate:.2%}, "
            f"actual={self.violation.actual_pass_rate:.2%})"
        )


class SLAAlertHandler:
    def __init__(self, monitor: SLAMonitor) -> None:
        if not isinstance(monitor, SLAMonitor):
            raise TypeError("monitor must be an SLAMonitor instance")
        self._monitor = monitor
        self._handlers: List[AlertHandler] = []
        self._breach_count: int = 0

    def add_handler(self, handler: AlertHandler) -> None:
        self._handlers.append(handler)

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    @property
    def breach_count(self) -> int:
        return self._breach_count

    def observe(self, result: CheckResult) -> None:
        violation = self._monitor.observe(result)
        if violation is None:
            return
        self._breach_count += 1
        alert = SLABreachAlert(violation=violation)
        # Wrap the alert in a synthetic failed CheckResult for handlers
        from pipewarden.checks import CheckResult as CR, CheckStatus
        synthetic = CR(
            check_name=result.check_name,
            status=CheckStatus.FAILED,
            message=repr(alert),
        )
        for handler in self._handlers:
            handler.send(synthetic)

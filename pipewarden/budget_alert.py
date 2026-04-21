"""Alert handler that fires when an error budget is exhausted."""
from __future__ import annotations

from typing import List

from pipewarden.alerts import AlertHandler
from pipewarden.budget import BudgetViolation
from pipewarden.budget_registry import BudgetRegistry
from pipewarden.checks import CheckResult


class BudgetExhaustedAlert:
    """Emitted when an error budget is exceeded."""

    def __init__(self, violation: BudgetViolation) -> None:
        self.violation = violation

    def __repr__(self) -> str:
        return f"BudgetExhaustedAlert(violation={self.violation!r})"


class BudgetAlertHandler:
    """Wraps a BudgetRegistry and dispatches alerts to downstream handlers."""

    def __init__(self, registry: BudgetRegistry) -> None:
        if not isinstance(registry, BudgetRegistry):
            raise TypeError("registry must be a BudgetRegistry")
        self._registry = registry
        self._handlers: List[AlertHandler] = []

    def add_handler(self, handler: AlertHandler) -> None:
        if not isinstance(handler, AlertHandler):
            raise TypeError("handler must be an AlertHandler")
        self._handlers.append(handler)

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def observe(self, result: CheckResult) -> None:
        """Record the result and fire alerts for any newly exhausted budgets."""
        self._registry.observe(result)
        budget = self._registry.get(result.check_name)
        if budget is not None and budget.exhausted:
            violation = budget.violation()
            if violation is not None:
                alert = BudgetExhaustedAlert(violation)
                for handler in self._handlers:
                    handler.send(result, extra={"budget_alert": alert})

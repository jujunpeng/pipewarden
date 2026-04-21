"""Registry that manages ErrorBudget instances per check."""
from __future__ import annotations

from typing import Dict, List

from pipewarden.budget import BudgetViolation, ErrorBudget
from pipewarden.checks import CheckResult


class BudgetRegistry:
    """Central store for per-check error budgets."""

    def __init__(
        self,
        default_max_failures: int = 3,
        default_window_seconds: float = 3600.0,
    ) -> None:
        if default_max_failures < 0:
            raise ValueError("default_max_failures must be >= 0")
        if default_window_seconds <= 0:
            raise ValueError("default_window_seconds must be positive")
        self._default_max_failures = default_max_failures
        self._default_window_seconds = default_window_seconds
        self._budgets: Dict[str, ErrorBudget] = {}

    @property
    def default_max_failures(self) -> int:
        return self._default_max_failures

    @property
    def default_window_seconds(self) -> float:
        return self._default_window_seconds

    def _get_or_create(self, check_name: str) -> ErrorBudget:
        if check_name not in self._budgets:
            self._budgets[check_name] = ErrorBudget(
                check_name=check_name,
                max_failures=self._default_max_failures,
                window_seconds=self._default_window_seconds,
            )
        return self._budgets[check_name]

    def set_budget(
        self,
        check_name: str,
        max_failures: int,
        window_seconds: float,
    ) -> None:
        """Override budget settings for a specific check."""
        self._budgets[check_name] = ErrorBudget(
            check_name=check_name,
            max_failures=max_failures,
            window_seconds=window_seconds,
        )

    def observe(self, result: CheckResult) -> None:
        budget = self._get_or_create(result.check_name)
        budget.observe(result)

    def violations(self) -> List[BudgetViolation]:
        return [
            v
            for b in self._budgets.values()
            if (v := b.violation()) is not None
        ]

    def get(self, check_name: str) -> ErrorBudget | None:
        return self._budgets.get(check_name)

    def reset(self, check_name: str) -> None:
        if check_name in self._budgets:
            self._budgets[check_name].reset()

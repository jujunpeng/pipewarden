"""Escalation policy: trigger a secondary handler if a check keeps failing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class EscalationPolicy:
    """Escalate to *handler* when a check has failed for *threshold* consecutive runs."""

    threshold: int
    handler: Callable[[CheckResult], None]
    _consecutive: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")

    def observe(self, result: CheckResult) -> bool:
        """Record *result* and escalate if the threshold is reached.

        Returns True if escalation was triggered.
        """
        name = result.check_name
        if result.status == CheckStatus.PASSED:
            self._consecutive[name] = 0
            return False

        count = self._consecutive.get(name, 0) + 1
        self._consecutive[name] = count

        if count >= self.threshold:
            self.handler(result)
            return True
        return False

    def consecutive_failures(self, check_name: str) -> int:
        """Return the current consecutive-failure count for *check_name*."""
        return self._consecutive.get(check_name, 0)

    def reset(self, check_name: str) -> None:
        """Manually reset the counter for *check_name*."""
        self._consecutive.pop(check_name, None)

"""Notification throttling to suppress repeated alerts within a cooldown window."""

from __future__ import annotations

import time
from typing import Callable, Dict, Optional

from pipewarden.pipeline import PipelineReport
from pipewarden.notifier import PipelineNotifier, NotifyFn


class ThrottledNotifier:
    """Wraps PipelineNotifier and suppresses repeated notifications within a cooldown period."""

    def __init__(self, notifier: PipelineNotifier, cooldown_seconds: float = 60.0) -> None:
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")
        self._notifier = notifier
        self._cooldown = cooldown_seconds
        self._last_fired: Dict[str, float] = {}

    @property
    def cooldown_seconds(self) -> float:
        return self._cooldown

    def notify(self, report: PipelineReport) -> list[str]:
        """Notify only rules whose cooldown has elapsed since last trigger."""
        now = time.monotonic()
        suppressed: set[str] = set()

        for rule in self._notifier._rules:
            last = self._last_fired.get(rule.name)
            if last is not None and (now - last) < self._cooldown:
                suppressed.add(rule.name)

        triggered = []
        for rule in self._notifier._rules:
            if rule.name in suppressed:
                continue
            if rule.matches(report):
                rule.callback(report)
                self._last_fired[rule.name] = now
                triggered.append(rule.name)

        return triggered

    def reset(self, rule_name: Optional[str] = None) -> None:
        """Reset cooldown state for a specific rule or all rules."""
        if rule_name is not None:
            self._last_fired.pop(rule_name, None)
        else:
            self._last_fired.clear()

    def is_throttled(self, rule_name: str) -> bool:
        """Return True if the rule is currently within its cooldown window."""
        last = self._last_fired.get(rule_name)
        if last is None:
            return False
        return (time.monotonic() - last) < self._cooldown

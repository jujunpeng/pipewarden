from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from pipewarden.trend import TrendTracker, TrendWindow
from pipewarden.alerts import AlertHandler
from pipewarden.checks import CheckResult


@dataclass
class TrendAlert:
    check_name: str
    kind: str  # 'degrading' or 'recovering'
    pass_rate: float
    window_size: int

    def __repr__(self) -> str:
        return (
            f"TrendAlert(check={self.check_name!r}, kind={self.kind!r}, "
            f"pass_rate={self.pass_rate:.2f}, window={self.window_size})"
        )


class TrendAlertHandler:
    """Wraps a TrendTracker and fires alerts when trends shift."""

    def __init__(
        self,
        tracker: TrendTracker,
        handlers: Optional[List[AlertHandler]] = None,
    ) -> None:
        self._tracker = tracker
        self._handlers: List[AlertHandler] = handlers or []

    def add_handler(self, handler: AlertHandler) -> None:
        self._handlers.append(handler)

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def observe(self, result: CheckResult) -> Optional[TrendAlert]:
        """Record result and return a TrendAlert if a trend change is detected."""
        self._tracker.record(result)
        window: TrendWindow = self._tracker.get(result.check_name)  # type: ignore

        alert: Optional[TrendAlert] = None
        if window.is_degrading:
            alert = TrendAlert(
                check_name=result.check_name,
                kind="degrading",
                pass_rate=window.pass_rate,
                window_size=window.size,
            )
        elif window.is_recovering:
            alert = TrendAlert(
                check_name=result.check_name,
                kind="recovering",
                pass_rate=window.pass_rate,
                window_size=window.size,
            )

        if alert is not None:
            self._dispatch(alert, result)

        return alert

    def _dispatch(self, alert: TrendAlert, result: CheckResult) -> None:
        for handler in self._handlers:
            try:
                handler.send(result)
            except Exception:
                pass

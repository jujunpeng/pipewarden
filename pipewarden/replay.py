"""Replay recorded CheckResults through alert handlers for testing or backfill."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from pipewarden.checks import CheckResult
from pipewarden.alerts import AlertHandler


@dataclass
class ReplayFilter:
    """Optional predicate to select which results to replay."""
    predicate: Callable[[CheckResult], bool]

    def matches(self, result: CheckResult) -> bool:
        try:
            return self.predicate(result)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"ReplayFilter(predicate={self.predicate!r})"


class ResultReplayer:
    """Replays a list of CheckResults through registered AlertHandlers."""

    def __init__(self) -> None:
        self._handlers: List[AlertHandler] = []
        self._replayed_count: int = 0
        self._skipped_count: int = 0

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    @property
    def replayed_count(self) -> int:
        return self._replayed_count

    @property
    def skipped_count(self) -> int:
        return self._skipped_count

    def add_handler(self, handler: AlertHandler) -> None:
        if not isinstance(handler, AlertHandler):
            raise TypeError("handler must be an AlertHandler instance")
        self._handlers.append(handler)

    def replay(
        self,
        results: List[CheckResult],
        replay_filter: ReplayFilter | None = None,
    ) -> int:
        """Replay results through all handlers. Returns number of results replayed."""
        replayed = 0
        for result in results:
            if replay_filter is not None and not replay_filter.matches(result):
                self._skipped_count += 1
                continue
            for handler in self._handlers:
                handler.send(result)
            replayed += 1
            self._replayed_count += 1
        return replayed

    def reset(self) -> None:
        self._replayed_count = 0
        self._skipped_count = 0

    def __repr__(self) -> str:
        return (
            f"ResultReplayer(handlers={self.handler_count}, "
            f"replayed={self._replayed_count}, skipped={self._skipped_count})"
        )

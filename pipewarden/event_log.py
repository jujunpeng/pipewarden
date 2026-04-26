"""Event log for recording significant pipeline lifecycle events."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Deque, Iterator, List, Optional


class EventKind(str, Enum):
    CHECK_PASSED = "check_passed"
    CHECK_FAILED = "check_failed"
    CHECK_ERROR = "check_error"
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_FINISHED = "pipeline_finished"
    ALERT_SENT = "alert_sent"


@dataclass(frozen=True)
class PipelineEvent:
    kind: EventKind
    check_name: Optional[str]
    message: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:  # pragma: no cover
        ts = self.recorded_at.isoformat()
        name = self.check_name or "<pipeline>"
        return f"PipelineEvent(kind={self.kind.value!r}, check={name!r}, at={ts!r})"


class EventLog:
    """Bounded in-memory log of pipeline events."""

    DEFAULT_MAX_SIZE = 500

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE) -> None:
        if max_size <= 0:
            raise ValueError(f"max_size must be positive, got {max_size}")
        self._max_size = max_size
        self._events: Deque[PipelineEvent] = deque(maxlen=max_size)

    @property
    def max_size(self) -> int:
        return self._max_size

    def record(self, event: PipelineEvent) -> None:
        """Append an event; oldest entry is dropped when capacity is exceeded."""
        if not isinstance(event, PipelineEvent):
            raise TypeError(f"Expected PipelineEvent, got {type(event).__name__}")
        self._events.append(event)

    def by_kind(self, kind: EventKind) -> List[PipelineEvent]:
        """Return all events matching *kind*."""
        return [e for e in self._events if e.kind == kind]

    def by_check(self, check_name: str) -> List[PipelineEvent]:
        """Return all events associated with *check_name*."""
        return [e for e in self._events if e.check_name == check_name]

    def all(self) -> List[PipelineEvent]:
        """Return a snapshot of all recorded events (oldest first)."""
        return list(self._events)

    def clear(self) -> None:
        """Remove all recorded events."""
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[PipelineEvent]:
        return iter(self._events)

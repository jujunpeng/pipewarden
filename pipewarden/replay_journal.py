"""Replay journal for recording and replaying pipeline check results.

The ReplayJournal persists a bounded sequence of CheckResult objects and
allows callers to replay them through any AlertHandler, useful for
post-incident analysis and testing alert pipelines against historical data.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Optional, Sequence

from .alerts import AlertHandler
from .checks import CheckResult


@dataclass
class JournalEntry:
    """A single entry in the replay journal."""

    result: CheckResult
    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"JournalEntry(check={self.result.check_name!r}, "
            f"status={self.result.status.value!r}, "
            f"recorded_at={self.recorded_at.isoformat()!r})"
        )


class ReplayJournal:
    """Bounded, ordered journal of CheckResult objects with replay support.

    Parameters
    ----------
    max_size:
        Maximum number of entries retained.  Oldest entries are evicted
        when the journal is full.  Must be a positive integer.
    """

    def __init__(self, max_size: int = 500) -> None:
        if max_size <= 0:
            raise ValueError(f"max_size must be a positive integer, got {max_size}")
        self._max_size = max_size
        self._entries: deque[JournalEntry] = deque(maxlen=max_size)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def max_size(self) -> int:
        """Maximum number of entries the journal retains."""
        return self._max_size

    @property
    def size(self) -> int:
        """Current number of entries in the journal."""
        return len(self._entries)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def record(
        self,
        result: CheckResult,
        tags: Iterable[str] = (),
    ) -> JournalEntry:
        """Append *result* to the journal and return the created entry."""
        entry = JournalEntry(result=result, tags=tuple(tags))
        self._entries.append(entry)
        return entry

    def clear(self) -> None:
        """Remove all entries from the journal."""
        self._entries.clear()

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def entries(
        self,
        *,
        check_name: Optional[str] = None,
        tag: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[JournalEntry]:
        """Return a filtered list of journal entries (oldest first).

        Parameters
        ----------
        check_name:
            If provided, only entries for this check name are returned.
        tag:
            If provided, only entries that carry this tag are returned.
        since:
            If provided, only entries recorded at or after this datetime
            are returned.
        """
        result: List[JournalEntry] = []
        for entry in self._entries:
            if check_name is not None and entry.result.check_name != check_name:
                continue
            if tag is not None and tag not in entry.tags:
                continue
            if since is not None and entry.recorded_at < since:
                continue
            result.append(entry)
        return result

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    def replay(
        self,
        handler: AlertHandler,
        *,
        check_name: Optional[str] = None,
        tag: Optional[str] = None,
        since: Optional[datetime] = None,
        transform: Optional[Callable[[CheckResult], CheckResult]] = None,
    ) -> int:
        """Send stored results through *handler*, returning the count sent.

        Parameters
        ----------
        handler:
            An :class:`~pipewarden.alerts.AlertHandler` that receives each
            replayed result via its ``send`` method.
        check_name / tag / since:
            Forwarded to :meth:`entries` to narrow the replay set.
        transform:
            Optional callable applied to each :class:`~pipewarden.checks.CheckResult`
            before it is dispatched.  Useful for stripping timestamps or
            injecting replay metadata.
        """
        matched = self.entries(check_name=check_name, tag=tag, since=since)
        for entry in matched:
            result = entry.result if transform is None else transform(entry.result)
            handler.send(result)
        return len(matched)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ReplayJournal(size={self.size}, max_size={self._max_size})"

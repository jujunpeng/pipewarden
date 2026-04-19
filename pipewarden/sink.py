"""Result sink: collects CheckResults and flushes them in batches."""
from __future__ import annotations

from typing import Callable, List

from pipewarden.checks import CheckResult


class ResultSink:
    """Buffers CheckResults and calls a flush handler when the batch is full."""

    def __init__(
        self,
        batch_size: int,
        on_flush: Callable[[List[CheckResult]], None],
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        self._batch_size = batch_size
        self._on_flush = on_flush
        self._buffer: List[CheckResult] = []
        self._total_flushed: int = 0

    @property
    def batch_size(self) -> int:
        return self._batch_size

    @property
    def pending(self) -> int:
        """Number of results waiting in the buffer."""
        return len(self._buffer)

    @property
    def total_flushed(self) -> int:
        """Total number of results that have been flushed."""
        return self._total_flushed

    def write(self, result: CheckResult) -> None:
        """Add a result; triggers flush when batch is full."""
        self._buffer.append(result)
        if len(self._buffer) >= self._batch_size:
            self.flush()

    def flush(self) -> None:
        """Flush all pending results immediately."""
        if not self._buffer:
            return
        batch = list(self._buffer)
        self._buffer.clear()
        self._total_flushed += len(batch)
        self._on_flush(batch)

    def reset(self) -> None:
        """Clear the buffer without flushing."""
        self._buffer.clear()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ResultSink(batch_size={self._batch_size}, "
            f"pending={self.pending}, total_flushed={self.total_flushed})"
        )

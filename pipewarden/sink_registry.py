"""Registry that routes CheckResults to named ResultSink instances."""
from __future__ import annotations

from typing import Dict, List

from pipewarden.checks import CheckResult
from pipewarden.sink import ResultSink


class SinkRegistry:
    """Maintains a collection of named sinks and fans out written results."""

    def __init__(self) -> None:
        self._sinks: Dict[str, ResultSink] = {}

    @property
    def sink_names(self) -> List[str]:
        return list(self._sinks.keys())

    def register(self, name: str, sink: ResultSink) -> None:
        """Register a sink under *name*. Raises if name already taken."""
        if name in self._sinks:
            raise KeyError(f"Sink '{name}' is already registered")
        self._sinks[name] = sink

    def unregister(self, name: str) -> None:
        """Remove a sink by name. Raises if not found."""
        if name not in self._sinks:
            raise KeyError(f"Sink '{name}' not found")
        del self._sinks[name]

    def get(self, name: str) -> ResultSink:
        """Return the sink registered under *name*."""
        if name not in self._sinks:
            raise KeyError(f"Sink '{name}' not found")
        return self._sinks[name]

    def write(self, result: CheckResult) -> None:
        """Fan out *result* to every registered sink."""
        for sink in self._sinks.values():
            sink.write(result)

    def flush_all(self) -> None:
        """Flush every registered sink."""
        for sink in self._sinks.values():
            sink.flush()

    def __len__(self) -> int:
        return len(self._sinks)

    def __repr__(self) -> str:  # pragma: no cover
        return f"SinkRegistry(sinks={self.sink_names})"

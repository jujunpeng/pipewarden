"""Renders a human-readable profiler summary."""
from __future__ import annotations
from pipewarden.profiler import CheckProfiler


class ProfilerReport:
    """Renders profiling data from a CheckProfiler."""

    def __init__(self, profiler: CheckProfiler) -> None:
        if not isinstance(profiler, CheckProfiler):
            raise TypeError("profiler must be a CheckProfiler")
        self._profiler = profiler

    def render(self) -> str:
        entries = self._profiler.all_entries()
        if not entries:
            return "No profiling data recorded."
        lines = [f"Profiler Report (threshold: {self._profiler.threshold_ms:.0f}ms)"]
        lines.append("-" * 40)
        for e in entries:
            flag = " [SLOW]" if e.is_slow else ""
            lines.append(f"  {e.check_name}: {e.duration_ms:.1f}ms{flag}")
        slow = self._profiler.slow_checks()
        lines.append("-" * 40)
        lines.append(f"Total: {len(entries)}  Slow: {len(slow)}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()

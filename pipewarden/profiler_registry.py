"""Registry that manages per-check profilers."""
from __future__ import annotations
from typing import Dict, List
from pipewarden.checks import CheckResult
from pipewarden.profiler import CheckProfiler, ProfileEntry


class ProfilerRegistry:
    """Holds one CheckProfiler per check name, sharing a common threshold."""

    def __init__(self, default_threshold_ms: float = 1000.0) -> None:
        if default_threshold_ms <= 0:
            raise ValueError("default_threshold_ms must be positive")
        self._default_threshold_ms = default_threshold_ms
        self._profilers: Dict[str, CheckProfiler] = {}

    @property
    def default_threshold_ms(self) -> float:
        return self._default_threshold_ms

    def _get_or_create(self, check_name: str) -> CheckProfiler:
        if check_name not in self._profilers:
            self._profilers[check_name] = CheckProfiler(self._default_threshold_ms)
        return self._profilers[check_name]

    def observe(self, result: CheckResult) -> ProfileEntry:
        profiler = self._get_or_create(result.check_name)
        return profiler.observe(result)

    def slow_checks(self) -> List[ProfileEntry]:
        slow: List[ProfileEntry] = []
        for p in self._profilers.values():
            slow.extend(p.slow_checks())
        return slow

    def get(self, check_name: str) -> CheckProfiler:
        if check_name not in self._profilers:
            raise KeyError(f"No profiler for check {check_name!r}")
        return self._profilers[check_name]

    def known_checks(self) -> List[str]:
        return list(self._profilers.keys())

    def reset_all(self) -> None:
        for p in self._profilers.values():
            p.reset()

    def __len__(self) -> int:
        return len(self._profilers)

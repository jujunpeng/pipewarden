"""Registry that manages WindowAggregator instances per check."""
from __future__ import annotations
from typing import Dict, List
from pipewarden.checks import CheckResult
from pipewarden.window_aggregator import WindowAggregator


class WindowRegistry:
    """Maintains one WindowAggregator per check name."""

    def __init__(self, default_max_size: int = 20) -> None:
        if default_max_size < 1:
            raise ValueError("default_max_size must be at least 1")
        self._default_max_size = default_max_size
        self._aggregators: Dict[str, WindowAggregator] = {}

    @property
    def default_max_size(self) -> int:
        return self._default_max_size

    def record(self, result: CheckResult) -> None:
        name = result.check_name
        if name not in self._aggregators:
            self._aggregators[name] = WindowAggregator(
                check_name=name, max_size=self._default_max_size
            )
        self._aggregators[name].record(result)

    def get(self, check_name: str) -> WindowAggregator:
        if check_name not in self._aggregators:
            raise KeyError(f"No window found for check '{check_name}'")
        return self._aggregators[check_name]

    def check_names(self) -> List[str]:
        return list(self._aggregators.keys())

    def __len__(self) -> int:
        return len(self._aggregators)

    def __repr__(self) -> str:
        return (
            f"WindowRegistry(default_max_size={self._default_max_size}, "
            f"checks={self.check_names()})"
        )

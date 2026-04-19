"""Cross-check result correlator for detecting related failures."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class CorrelationGroup:
    """A named group of check names expected to correlate."""
    name: str
    check_names: List[str]
    condition: Callable[[List[CheckResult]], bool]

    def matches(self, results: List[CheckResult]) -> bool:
        try:
            return self.condition(results)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"CorrelationGroup(name={self.name!r}, checks={self.check_names})"


@dataclass
class CorrelationAlert:
    group_name: str
    triggered_results: List[CheckResult]

    def __repr__(self) -> str:
        names = [r.check_name for r in self.triggered_results]
        return f"CorrelationAlert(group={self.group_name!r}, checks={names})"


class ResultCorrelator:
    """Evaluates correlation groups against a set of results."""

    def __init__(self) -> None:
        self._groups: List[CorrelationGroup] = []

    @property
    def group_count(self) -> int:
        return len(self._groups)

    def add_group(self, group: CorrelationGroup) -> None:
        if not isinstance(group, CorrelationGroup):
            raise TypeError("Expected a CorrelationGroup instance.")
        self._groups.append(group)

    def evaluate(self, results: List[CheckResult]) -> List[CorrelationAlert]:
        """Return alerts for any groups whose condition is triggered."""
        alerts: List[CorrelationAlert] = []
        by_name = {r.check_name: r for r in results}
        for group in self._groups:
            relevant = [by_name[n] for n in group.check_names if n in by_name]
            if relevant and group.matches(relevant):
                alerts.append(CorrelationAlert(group.name, relevant))
        return alerts

    def clear(self) -> None:
        self._groups.clear()

    def __repr__(self) -> str:
        return f"ResultCorrelator(groups={self.group_count})"

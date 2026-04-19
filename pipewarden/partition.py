"""Partition check results into named buckets based on predicates."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List
from pipewarden.checks import CheckResult


@dataclass
class Partition:
    name: str
    predicate: Callable[[CheckResult], bool]
    _results: List[CheckResult] = field(default_factory=list, init=False, repr=False)

    def matches(self, result: CheckResult) -> bool:
        try:
            return bool(self.predicate(result))
        except Exception:
            return False

    def add(self, result: CheckResult) -> None:
        self._results.append(result)

    def results(self) -> List[CheckResult]:
        return list(self._results)

    def __len__(self) -> int:
        return len(self._results)

    def __repr__(self) -> str:
        return f"Partition(name={self.name!r}, count={len(self)})"


class ResultPartitioner:
    """Routes CheckResults into named Partition buckets."""

    def __init__(self) -> None:
        self._partitions: List[Partition] = []
        self._unmatched: List[CheckResult] = []

    def add_partition(self, name: str, predicate: Callable[[CheckResult], bool]) -> None:
        if any(p.name == name for p in self._partitions):
            raise ValueError(f"Partition {name!r} already registered.")
        self._partitions.append(Partition(name=name, predicate=predicate))

    def route(self, result: CheckResult) -> None:
        matched = False
        for partition in self._partitions:
            if partition.matches(result):
                partition.add(result)
                matched = True
        if not matched:
            self._unmatched.append(result)

    def get(self, name: str) -> Partition:
        for p in self._partitions:
            if p.name == name:
                return p
        raise KeyError(f"No partition named {name!r}.")

    def partition_names(self) -> List[str]:
        return [p.name for p in self._partitions]

    def unmatched(self) -> List[CheckResult]:
        return list(self._unmatched)

    def __len__(self) -> int:
        return len(self._partitions)

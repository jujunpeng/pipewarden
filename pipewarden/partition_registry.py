"""Registry of named ResultPartitioner instances."""
from __future__ import annotations
from typing import Dict
from pipewarden.partition import ResultPartitioner


class PartitionRegistry:
    """Stores and retrieves named ResultPartitioner instances."""

    def __init__(self) -> None:
        self._store: Dict[str, ResultPartitioner] = {}

    def register(self, name: str, partitioner: ResultPartitioner) -> None:
        if not isinstance(partitioner, ResultPartitioner):
            raise TypeError("partitioner must be a ResultPartitioner.")
        if name in self._store:
            raise ValueError(f"Partitioner {name!r} already registered.")
        self._store[name] = partitioner

    def get(self, name: str) -> ResultPartitioner:
        if name not in self._store:
            raise KeyError(f"No partitioner named {name!r}.")
        return self._store[name]

    def unregister(self, name: str) -> None:
        if name not in self._store:
            raise KeyError(f"No partitioner named {name!r}.")
        del self._store[name]

    def names(self):
        return list(self._store.keys())

    def __len__(self) -> int:
        return len(self._store)

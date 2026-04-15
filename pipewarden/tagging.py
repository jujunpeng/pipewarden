"""Tag-based filtering and grouping of health check results."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, FrozenSet, Iterable, List

from pipewarden.checks import CheckResult, CheckStatus


class TagIndex:
    """Indexes CheckResult objects by their tags for fast lookup."""

    def __init__(self) -> None:
        self._index: Dict[str, List[CheckResult]] = defaultdict(list)
        self._all: List[CheckResult] = []

    def add(self, result: CheckResult, tags: Iterable[str]) -> None:
        """Register a result under each of its tags."""
        tag_set = frozenset(tags)
        self._all.append(result)
        for tag in tag_set:
            self._index[tag].append(result)

    def get_by_tag(self, tag: str) -> List[CheckResult]:
        """Return all results that carry *tag*."""
        return list(self._index.get(tag, []))

    def get_by_tags(self, tags: Iterable[str], match_all: bool = True) -> List[CheckResult]:
        """Return results matching *tags*.

        Args:
            tags: Collection of tag strings to filter by.
            match_all: When ``True`` (default) results must carry **all** tags;
                       when ``False`` results carrying **any** tag are returned.
        """
        tag_list = list(tags)
        if not tag_list:
            return list(self._all)

        sets = [set(self.get_by_tag(t)) for t in tag_list]
        if match_all:
            combined = sets[0].intersection(*sets[1:])
        else:
            combined: set = set()
            for s in sets:
                combined |= s

        # Preserve insertion order.
        return [r for r in self._all if r in combined]

    def known_tags(self) -> FrozenSet[str]:
        """Return the set of all tags currently in the index."""
        return frozenset(self._index.keys())

    def group_by_tag(self) -> Dict[str, List[CheckResult]]:
        """Return a copy of the internal tag → results mapping."""
        return {tag: list(results) for tag, results in self._index.items()}

    def failed_by_tag(self, tag: str) -> List[CheckResult]:
        """Convenience: results for *tag* whose status is not PASSED."""
        return [
            r for r in self.get_by_tag(tag)
            if r.status != CheckStatus.PASSED
        ]

    def __len__(self) -> int:
        return len(self._all)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TagIndex(results={len(self._all)}, tags={len(self._index)})"

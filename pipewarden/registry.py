"""Global check registry for auto-discovering and grouping health checks."""

from __future__ import annotations

from typing import Dict, List, Optional

from pipewarden.checks import HealthCheck


class CheckRegistry:
    """A simple registry that maps tag names to :class:`HealthCheck` instances.

    Checks can be registered with one or more tags so that callers can retrieve
    subsets of checks (e.g. all checks belonging to a particular pipeline or
    data domain).
    """

    def __init__(self) -> None:
        self._checks: Dict[str, HealthCheck] = {}
        self._tags: Dict[str, List[str]] = {}  # check_name -> [tag, ...]

    def register(
        self,
        check: HealthCheck,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Add *check* to the registry, optionally associating *tags* with it."""
        if check.name in self._checks:
            raise ValueError(f"A check named '{check.name}' is already registered.")
        self._checks[check.name] = check
        self._tags[check.name] = list(tags or [])

    def unregister(self, name: str) -> None:
        """Remove a check by name; raises :class:`KeyError` if not found."""
        del self._checks[name]
        del self._tags[name]

    def get(self, name: str) -> HealthCheck:
        """Return the check registered under *name*."""
        return self._checks[name]

    def all_checks(self) -> List[HealthCheck]:
        """Return every registered check."""
        return list(self._checks.values())

    def checks_by_tag(self, tag: str) -> List[HealthCheck]:
        """Return all checks that carry *tag*."""
        return [
            self._checks[name]
            for name, tags in self._tags.items()
            if tag in tags
        ]

    def tags_for(self, name: str) -> List[str]:
        """Return the tags associated with check *name*."""
        return list(self._tags[name])

    def __len__(self) -> int:
        return len(self._checks)

    def __contains__(self, name: str) -> bool:
        return name in self._checks


# Module-level default registry
default_registry: CheckRegistry = CheckRegistry()

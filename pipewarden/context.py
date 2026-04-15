"""Execution context for health checks, carrying metadata and tags."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CheckContext:
    """Carries runtime metadata and user-defined tags for a single check execution."""

    run_id: str
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: Optional[float] = None

    def with_tag(self, key: str, value: str) -> "CheckContext":
        """Return a new context with an additional tag."""
        new_tags = {**self.tags, key: value}
        return CheckContext(
            run_id=self.run_id,
            tags=new_tags,
            metadata=self.metadata,
            timeout_seconds=self.timeout_seconds,
        )

    def with_metadata(self, key: str, value: Any) -> "CheckContext":
        """Return a new context with an additional metadata entry."""
        new_meta = {**self.metadata, key: value}
        return CheckContext(
            run_id=self.run_id,
            tags=self.tags,
            metadata=new_meta,
            timeout_seconds=self.timeout_seconds,
        )

    def has_tag(self, key: str) -> bool:
        """Return True if the given tag key is present."""
        return key in self.tags

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CheckContext(run_id={self.run_id!r}, tags={self.tags!r}, "
            f"timeout_seconds={self.timeout_seconds!r})"
        )


def make_context(
    run_id: str,
    tags: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timeout_seconds: Optional[float] = None,
) -> CheckContext:
    """Convenience factory for creating a CheckContext."""
    return CheckContext(
        run_id=run_id,
        tags=tags or {},
        metadata=metadata or {},
        timeout_seconds=timeout_seconds,
    )

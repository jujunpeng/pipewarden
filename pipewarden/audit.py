"""Audit log for pipeline check executions."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class AuditEntry:
    check_name: str
    status: CheckStatus
    message: str
    duration_ms: Optional[float]
    recorded_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"AuditEntry(check={self.check_name!r}, status={self.status.value}, "
            f"recorded_at={self.recorded_at.isoformat()})"
        )


class AuditLog:
    """Append-only log of CheckResult audit entries."""

    def __init__(self, max_size: int = 500) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._max_size = max_size
        self._entries: List[AuditEntry] = []

    @property
    def max_size(self) -> int:
        return self._max_size

    def record(self, result: CheckResult) -> None:
        entry = AuditEntry(
            check_name=result.check_name,
            status=result.status,
            message=result.message,
            duration_ms=result.duration_ms,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_size:
            self._entries.pop(0)

    def all(self) -> List[AuditEntry]:
        return list(self._entries)

    def for_check(self, check_name: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.check_name == check_name]

    def failures(self) -> List[AuditEntry]:
        return [e for e in self._entries if e.status != CheckStatus.PASSED]

    def __len__(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

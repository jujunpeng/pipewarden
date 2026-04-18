from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class Checkpoint:
    """Records the last known good result for a named check."""
    check_name: str
    result: CheckResult
    saved_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return f"Checkpoint(check={self.check_name!r}, status={self.result.status.value}, saved_at={self.saved_at.isoformat()})"


class CheckpointStore:
    """Stores the most recent passing checkpoint for each check."""

    def __init__(self) -> None:
        self._store: Dict[str, Checkpoint] = {}

    @property
    def size(self) -> int:
        return len(self._store)

    def save(self, result: CheckResult) -> None:
        """Save a checkpoint only when the result is PASSED."""
        if result.status != CheckStatus.PASSED:
            return
        self._store[result.check_name] = Checkpoint(
            check_name=result.check_name,
            result=result,
        )

    def get(self, check_name: str) -> Optional[Checkpoint]:
        """Return the latest passing checkpoint for a check, or None."""
        return self._store.get(check_name)

    def has(self, check_name: str) -> bool:
        return check_name in self._store

    def clear(self, check_name: str) -> None:
        """Remove the checkpoint for a specific check."""
        self._store.pop(check_name, None)

    def all_names(self) -> list:
        return list(self._store.keys())

    def reset(self) -> None:
        self._store.clear()

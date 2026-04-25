"""Result fingerprinting — assigns stable hash identifiers to CheckResults
for deduplication, correlation, and change tracking."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewarden.checks import CheckResult, CheckStatus


def _fingerprint(result: CheckResult) -> str:
    """Return a stable SHA-256 fingerprint for a CheckResult.

    The fingerprint is derived from the check name and status only so that
    two results for the same check with the same status always share a
    fingerprint, regardless of when they were recorded.
    """
    payload = json.dumps(
        {"check_name": result.check_name, "status": result.status.value},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class FingerprintEntry:
    """Associates a fingerprint with the result that produced it."""

    fingerprint: str
    result: CheckResult

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FingerprintEntry(fingerprint={self.fingerprint[:8]!r}, "
            f"check={self.result.check_name!r}, status={self.result.status.value!r})"
        )


class FingerprintIndex:
    """Maintains a mapping from fingerprint → list of matching results.

    Useful for grouping results that share the same (check_name, status)
    combination across multiple pipeline runs.
    """

    def __init__(self) -> None:
        self._index: Dict[str, List[CheckResult]] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, result: CheckResult) -> str:
        """Index *result* and return its fingerprint."""
        fp = _fingerprint(result)
        self._index.setdefault(fp, []).append(result)
        return fp

    def clear(self) -> None:
        """Remove all entries from the index."""
        self._index.clear()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, fingerprint: str) -> List[CheckResult]:
        """Return all results that share *fingerprint* (may be empty)."""
        return list(self._index.get(fingerprint, []))

    def fingerprint_for(self, result: CheckResult) -> str:
        """Return the fingerprint for *result* without indexing it."""
        return _fingerprint(result)

    @property
    def known_fingerprints(self) -> List[str]:
        """Return all fingerprints currently in the index."""
        return list(self._index.keys())

    def __len__(self) -> int:
        return sum(len(v) for v in self._index.values())

    def __repr__(self) -> str:  # pragma: no cover
        return f"FingerprintIndex(fingerprints={len(self._index)}, total={len(self)})"

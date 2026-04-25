"""Shadow mode runner: executes checks silently and compares results to a reference run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class ShadowDiff:
    """Difference between a live result and its shadow counterpart."""

    check_name: str
    live_status: CheckStatus
    shadow_status: CheckStatus

    @property
    def diverged(self) -> bool:
        """Return True when live and shadow statuses differ."""
        return self.live_status != self.shadow_status

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ShadowDiff(check={self.check_name!r}, "
            f"live={self.live_status.value}, shadow={self.shadow_status.value})"
        )


class ShadowRunner:
    """Run a shadow (duplicate) check alongside the live check and compare outcomes.

    Parameters
    ----------
    shadow_fn:
        Callable that accepts a check name and returns a :class:`CheckResult`.
        This is the *shadow* implementation whose results are never surfaced to
        production alerting — only divergences are reported.
    """

    def __init__(self, shadow_fn: Callable[[str], CheckResult]) -> None:
        if not callable(shadow_fn):
            raise TypeError("shadow_fn must be callable")
        self._shadow_fn = shadow_fn
        self._diffs: List[ShadowDiff] = []
        self._divergence_count: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def divergence_count(self) -> int:
        """Total number of divergences observed since creation."""
        return self._divergence_count

    def observe(self, live_result: CheckResult) -> Optional[ShadowDiff]:
        """Run the shadow function for *live_result* and return a diff if statuses diverge.

        Parameters
        ----------
        live_result:
            The authoritative result produced by the live pipeline.

        Returns
        -------
        :class:`ShadowDiff` when the shadow status differs from the live status,
        ``None`` otherwise.
        """
        try:
            shadow_result = self._shadow_fn(live_result.check_name)
        except Exception:
            # Shadow failures must never affect the live pipeline.
            return None

        diff = ShadowDiff(
            check_name=live_result.check_name,
            live_status=live_result.status,
            shadow_status=shadow_result.status,
        )
        if diff.diverged:
            self._divergence_count += 1
            self._diffs.append(diff)
            return diff
        return None

    def diffs(self) -> List[ShadowDiff]:
        """Return a copy of all recorded divergences."""
        return list(self._diffs)

    def reset(self) -> None:
        """Clear recorded divergences and reset the counter."""
        self._diffs.clear()
        self._divergence_count = 0

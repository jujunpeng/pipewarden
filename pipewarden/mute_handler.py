"""Alert handler wrapper that skips delivery for muted check results."""
from __future__ import annotations

from pipewarden.alerts import AlertHandler
from pipewarden.checks import CheckResult
from pipewarden.mute import MuteRegistry


class MutedAlertHandler:
    """Wraps an AlertHandler and suppresses sends for muted results.

    Parameters
    ----------
    handler:
        The underlying AlertHandler to delegate to when not muted.
    registry:
        The MuteRegistry used to decide whether to suppress a result.
    """

    def __init__(self, handler: AlertHandler, registry: MuteRegistry) -> None:
        if not callable(getattr(handler, "send", None)):
            raise TypeError("handler must implement a send(result) method")
        if not isinstance(registry, MuteRegistry):
            raise TypeError("registry must be a MuteRegistry instance")
        self._handler = handler
        self._registry = registry
        self._suppressed_count = 0

    @property
    def suppressed_count(self) -> int:
        """Number of alerts suppressed so far."""
        return self._suppressed_count

    def send(self, result: CheckResult) -> None:
        """Forward the alert unless the result is muted."""
        if self._registry.is_muted(result):
            self._suppressed_count += 1
            return
        self._handler.send(result)

    def reset_count(self) -> None:
        """Reset the suppressed alert counter."""
        self._suppressed_count = 0

    def __repr__(self) -> str:
        return (
            f"MutedAlertHandler(handler={self._handler!r}, "
            f"suppressed={self._suppressed_count})"
        )

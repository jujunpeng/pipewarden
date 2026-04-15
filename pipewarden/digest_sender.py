"""Sends a rendered digest via registered alert handlers."""

from __future__ import annotations

from typing import List

from pipewarden.alerts import AlertHandler
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.digest import PipelineDigest


class DigestSender:
    """Renders a PipelineDigest and forwards it through AlertHandlers."""

    def __init__(self, handlers: List[AlertHandler] | None = None) -> None:
        self._handlers: List[AlertHandler] = list(handlers) if handlers else []

    def add_handler(self, handler: AlertHandler) -> None:
        """Register an additional alert handler."""
        self._handlers.append(handler)

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def send(self, digest: PipelineDigest) -> None:
        """Render *digest* and dispatch the summary via every registered handler."""
        if not self._handlers:
            return

        rendered = digest.render()
        # Wrap the digest text in a synthetic CheckResult so existing
        # AlertHandler.send signatures are satisfied without changes.
        synthetic = CheckResult(
            check_name="__digest__",
            status=CheckStatus.FAILED,
            message=rendered,
            duration_ms=0.0,
        )
        for handler in self._handlers:
            handler.send(synthetic)

    def __repr__(self) -> str:  # pragma: no cover
        return f"DigestSender(handlers={self.handler_count})"

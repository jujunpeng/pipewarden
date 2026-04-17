"""Hook that automatically records CheckResults into an AuditLog."""
from __future__ import annotations
from pipewarden.alerts import AlertHandler
from pipewarden.audit import AuditLog
from pipewarden.checks import CheckResult


class AuditHook(AlertHandler):
    """AlertHandler that records every result into an AuditLog.

    Can be registered with CheckRunner.add_handler so all results
    are automatically audited without changing pipeline logic.
    """

    def __init__(self, audit_log: AuditLog | None = None) -> None:
        self._log = audit_log if audit_log is not None else AuditLog()

    @property
    def log(self) -> AuditLog:
        return self._log

    def send(self, result: CheckResult) -> None:
        """Record the result regardless of status."""
        self._log.record(result)

    def __repr__(self) -> str:
        return f"AuditHook(entries={len(self._log)})"

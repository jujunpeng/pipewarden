"""Core health check primitives for pipewarden."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class CheckStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class CheckResult:
    """Holds the outcome of a single health check execution."""

    name: str
    status: CheckStatus
    message: str = ""
    value: Any = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def passed(self) -> bool:
        return self.status == CheckStatus.PASSED

    def __repr__(self) -> str:
        return (
            f"CheckResult(name={self.name!r}, status={self.status.value}, "
            f"message={self.message!r})"
        )


class HealthCheck:
    """Defines a named health check backed by a callable predicate."""

    def __init__(
        self,
        name: str,
        predicate: Callable[[], bool],
        description: str = "",
        failure_message: Optional[str] = None,
    ) -> None:
        if not callable(predicate):
            raise TypeError("predicate must be callable")
        self.name = name
        self.predicate = predicate
        self.description = description
        self.failure_message = failure_message or f"Check '{name}' failed."

    def run(self) -> CheckResult:
        """Execute the predicate and return a CheckResult."""
        try:
            passed = bool(self.predicate())
            status = CheckStatus.PASSED if passed else CheckStatus.FAILED
            message = "" if passed else self.failure_message
            return CheckResult(name=self.name, status=status, message=message)
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                name=self.name,
                status=CheckStatus.ERROR,
                message=f"Exception during check: {exc}",
            )

    def __repr__(self) -> str:
        return f"HealthCheck(name={self.name!r}, description={self.description!r})"

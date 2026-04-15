"""Retry logic for health checks that may transiently fail."""

from __future__ import annotations

import time
from typing import Callable, Optional

from pipewarden.checks import CheckResult, CheckStatus, HealthCheck


class RetryPolicy:
    """Defines how many times and how often a failing check should be retried."""

    def __init__(self, max_attempts: int = 3, delay_seconds: float = 0.0) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        self._max_attempts = max_attempts
        self._delay_seconds = delay_seconds

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    @property
    def delay_seconds(self) -> float:
        return self._delay_seconds

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RetryPolicy(max_attempts={self._max_attempts}, "
            f"delay_seconds={self._delay_seconds})"
        )


class RetryRunner:
    """Runs a HealthCheck with a RetryPolicy, retrying on FAILED or ERROR status."""

    def __init__(
        self,
        policy: RetryPolicy,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ) -> None:
        self._policy = policy
        self._sleep_fn: Callable[[float], None] = sleep_fn or time.sleep

    @property
    def policy(self) -> RetryPolicy:
        return self._policy

    def run(self, check: HealthCheck) -> CheckResult:
        """Execute *check*, retrying up to policy.max_attempts times.

        Returns the last result regardless of its status.
        """
        result: Optional[CheckResult] = None
        for attempt in range(1, self._policy.max_attempts + 1):
            result = check.run()
            if result.status == CheckStatus.PASSED:
                return result
            if attempt < self._policy.max_attempts and self._policy.delay_seconds > 0:
                self._sleep_fn(self._policy.delay_seconds)
        assert result is not None
        return result

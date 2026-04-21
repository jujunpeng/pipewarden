"""Registry that manages per-check quotas with a shared default configuration."""
from __future__ import annotations

from typing import Dict, Optional

from pipewarden.quota import CheckQuota, QuotaViolation


class QuotaRegistry:
    """Manages CheckQuota instances keyed by check name."""

    def __init__(
        self,
        default_limit: int = 60,
        default_window_seconds: float = 60.0,
    ) -> None:
        if default_limit <= 0:
            raise ValueError("default_limit must be a positive integer")
        if default_window_seconds <= 0:
            raise ValueError("default_window_seconds must be positive")
        self._default_limit = default_limit
        self._default_window_seconds = default_window_seconds
        self._quotas: Dict[str, CheckQuota] = {}
        self._overrides: Dict[str, tuple[int, float]] = {}

    @property
    def default_limit(self) -> int:
        return self._default_limit

    @property
    def default_window_seconds(self) -> float:
        return self._default_window_seconds

    def set_override(self, check_name: str, limit: int, window_seconds: float) -> None:
        """Override quota parameters for a specific check."""
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._overrides[check_name] = (limit, window_seconds)
        # Reset existing quota so new params take effect immediately
        self._quotas.pop(check_name, None)

    def remove_override(self, check_name: str) -> None:
        self._overrides.pop(check_name, None)
        self._quotas.pop(check_name, None)

    def _get_or_create(self, check_name: str) -> CheckQuota:
        if check_name not in self._quotas:
            limit, window = self._overrides.get(
                check_name, (self._default_limit, self._default_window_seconds)
            )
            self._quotas[check_name] = CheckQuota(check_name, limit, window)
        return self._quotas[check_name]

    def is_allowed(self, check_name: str) -> bool:
        return self._get_or_create(check_name).is_allowed()

    def record(self, check_name: str) -> None:
        self._get_or_create(check_name).record()

    def violation(self, check_name: str) -> QuotaViolation:
        return self._get_or_create(check_name).violation()

    def quota_for(self, check_name: str) -> CheckQuota:
        return self._get_or_create(check_name)

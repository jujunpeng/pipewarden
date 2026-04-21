from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class SLAViolation:
    check_name: str
    required_pass_rate: float
    actual_pass_rate: float
    window_size: int
    recorded_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"SLAViolation(check={self.check_name!r}, "
            f"required={self.required_pass_rate:.2%}, "
            f"actual={self.actual_pass_rate:.2%})"
        )


@dataclass
class SLAPolicy:
    check_name: str
    required_pass_rate: float
    window_size: int = 10

    def __post_init__(self) -> None:
        if not (0.0 <= self.required_pass_rate <= 1.0):
            raise ValueError("required_pass_rate must be between 0.0 and 1.0")
        if self.window_size < 1:
            raise ValueError("window_size must be at least 1")

    def __repr__(self) -> str:
        return (
            f"SLAPolicy(check={self.check_name!r}, "
            f"required={self.required_pass_rate:.2%}, "
            f"window={self.window_size})"
        )


class SLAMonitor:
    def __init__(self) -> None:
        self._policies: dict[str, SLAPolicy] = {}
        self._history: dict[str, List[CheckResult]] = {}

    def add_policy(self, policy: SLAPolicy) -> None:
        self._policies[policy.check_name] = policy
        if policy.check_name not in self._history:
            self._history[policy.check_name] = []

    def observe(self, result: CheckResult) -> Optional[SLAViolation]:
        name = result.check_name
        if name not in self._policies:
            return None
        policy = self._policies[name]
        history = self._history[name]
        history.append(result)
        if len(history) > policy.window_size:
            history.pop(0)
        if len(history) < policy.window_size:
            return None
        passed = sum(1 for r in history if r.status == CheckStatus.PASSED)
        actual_rate = passed / len(history)
        if actual_rate < policy.required_pass_rate:
            return SLAViolation(
                check_name=name,
                required_pass_rate=policy.required_pass_rate,
                actual_pass_rate=actual_rate,
                window_size=policy.window_size,
            )
        return None

    def policy_names(self) -> List[str]:
        return list(self._policies.keys())

    def reset(self, check_name: str) -> None:
        if check_name in self._history:
            self._history[check_name].clear()

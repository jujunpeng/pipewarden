from __future__ import annotations

from typing import List

from pipewarden.sla import SLAMonitor, SLAViolation


class SLAReport:
    def __init__(self, monitor: SLAMonitor, violations: List[SLAViolation]) -> None:
        if not isinstance(monitor, SLAMonitor):
            raise TypeError("monitor must be an SLAMonitor instance")
        self._monitor = monitor
        self._violations = list(violations)

    @property
    def violation_count(self) -> int:
        return len(self._violations)

    @property
    def violations(self) -> List[SLAViolation]:
        return list(self._violations)

    @property
    def passed(self) -> bool:
        return len(self._violations) == 0

    def render(self) -> str:
        lines: List[str] = []
        status = "OK" if self.passed else "VIOLATED"
        lines.append(f"SLA Report [{status}]")
        lines.append(f"Policies monitored : {len(self._monitor.policy_names())}")
        lines.append(f"Violations         : {self.violation_count}")
        if self._violations:
            lines.append("")
            lines.append("Violations:")
            for v in self._violations:
                lines.append(
                    f"  - {v.check_name}: required {v.required_pass_rate:.2%}, "
                    f"actual {v.actual_pass_rate:.2%} "
                    f"(window={v.window_size})"
                )
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()

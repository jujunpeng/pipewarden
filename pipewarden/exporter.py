"""Export pipeline metrics and history to various formats (JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from pipewarden.checks import CheckResult
    from pipewarden.metrics import CheckMetrics


class MetricsExporter:
    """Serialises CheckMetrics and CheckResult history to JSON or CSV."""

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    def to_json(self, metrics: "CheckMetrics", results: List["CheckResult"]) -> str:
        """Return a JSON string containing metrics and per-result history."""
        payload = {
            "metrics": {
                "pass_rate": metrics.pass_rate,
                "avg_duration_ms": metrics.avg_duration_ms,
                "total_runs": metrics.total_runs,
                "total_passed": metrics.total_passed,
                "total_failed": metrics.total_failed,
                "total_errors": metrics.total_errors,
            },
            "history": [self._result_to_dict(r) for r in results],
        }
        return json.dumps(payload, indent=2, default=str)

    # ------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------

    def to_csv(self, results: List["CheckResult"]) -> str:
        """Return a CSV string with one row per CheckResult."""
        buf = io.StringIO()
        fieldnames = ["name", "status", "message", "duration_ms", "timestamp"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for result in results:
            writer.writerow(self._result_to_dict(result))
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _result_to_dict(result: "CheckResult") -> dict:
        return {
            "name": result.name,
            "status": result.status.value,
            "message": result.message or "",
            "duration_ms": result.duration_ms,
            "timestamp": result.timestamp.isoformat() if result.timestamp else "",
        }

"""Tests for pipewarden.exporter.MetricsExporter."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.exporter import MetricsExporter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(name: str, status: CheckStatus, duration_ms: float = 10.0) -> CheckResult:
    r = CheckResult(
        name=name,
        status=status,
        message="ok" if status == CheckStatus.PASSED else "fail",
        duration_ms=duration_ms,
    )
    r.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return r


def _make_metrics(pass_rate=1.0, avg_duration_ms=5.0, total_runs=3,
                  total_passed=3, total_failed=0, total_errors=0):
    m = MagicMock()
    m.pass_rate = pass_rate
    m.avg_duration_ms = avg_duration_ms
    m.total_runs = total_runs
    m.total_passed = total_passed
    m.total_failed = total_failed
    m.total_errors = total_errors
    return m


# ---------------------------------------------------------------------------
# JSON tests
# ---------------------------------------------------------------------------

class TestMetricsExporterJSON:
    def setup_method(self):
        self.exporter = MetricsExporter()
        self.results = [
            _make_result("check_a", CheckStatus.PASSED),
            _make_result("check_b", CheckStatus.FAILED, duration_ms=20.0),
        ]
        self.metrics = _make_metrics(pass_rate=0.5, total_runs=2,
                                     total_passed=1, total_failed=1)

    def test_to_json_returns_string(self):
        out = self.exporter.to_json(self.metrics, self.results)
        assert isinstance(out, str)

    def test_to_json_is_valid_json(self):
        out = self.exporter.to_json(self.metrics, self.results)
        parsed = json.loads(out)
        assert "metrics" in parsed
        assert "history" in parsed

    def test_to_json_metrics_values(self):
        out = json.loads(self.exporter.to_json(self.metrics, self.results))
        assert out["metrics"]["pass_rate"] == 0.5
        assert out["metrics"]["total_runs"] == 2

    def test_to_json_history_length(self):
        out = json.loads(self.exporter.to_json(self.metrics, self.results))
        assert len(out["history"]) == 2

    def test_to_json_history_fields(self):
        out = json.loads(self.exporter.to_json(self.metrics, self.results))
        row = out["history"][0]
        assert set(row.keys()) == {"name", "status", "message", "duration_ms", "timestamp"}


# ---------------------------------------------------------------------------
# CSV tests
# ---------------------------------------------------------------------------

class TestMetricsExporterCSV:
    def setup_method(self):
        self.exporter = MetricsExporter()
        self.results = [
            _make_result("check_a", CheckStatus.PASSED, 5.0),
            _make_result("check_b", CheckStatus.FAILED, 15.0),
        ]

    def test_to_csv_returns_string(self):
        out = self.exporter.to_csv(self.results)
        assert isinstance(out, str)

    def test_to_csv_has_header(self):
        out = self.exporter.to_csv(self.results)
        first_line = out.splitlines()[0]
        assert "name" in first_line and "status" in first_line

    def test_to_csv_row_count(self):
        out = self.exporter.to_csv(self.results)
        rows = list(csv.DictReader(io.StringIO(out)))
        assert len(rows) == 2

    def test_to_csv_values(self):
        out = self.exporter.to_csv(self.results)
        rows = list(csv.DictReader(io.StringIO(out)))
        assert rows[0]["name"] == "check_a"
        assert rows[0]["status"] == "passed"
        assert rows[1]["status"] == "failed"

    def test_to_csv_empty_results(self):
        out = self.exporter.to_csv([])
        rows = list(csv.DictReader(io.StringIO(out)))
        assert rows == []

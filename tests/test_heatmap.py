"""Tests for CheckHeatmap and HeatmapReporter."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.heatmap import CheckHeatmap, HeatmapCell
from pipewarden.heatmap_reporter import HeatmapReporter


def _make_result(
    check_name: str,
    status: CheckStatus,
    ts: datetime,
    message: str = "",
    duration_ms: float = 10.0,
) -> CheckResult:
    return CheckResult(
        check_name=check_name,
        status=status,
        message=message,
        duration_ms=duration_ms,
        timestamp=ts,
    )


TS_A = datetime(2024, 6, 1, 9, 15, 0, tzinfo=timezone.utc)
TS_B = datetime(2024, 6, 1, 9, 45, 0, tzinfo=timezone.utc)  # same hour as A
TS_C = datetime(2024, 6, 1, 10, 5, 0, tzinfo=timezone.utc)  # different hour


class TestCheckHeatmap:
    def setup_method(self) -> None:
        self.heatmap = CheckHeatmap()

    def test_raises_on_empty_bucket_format(self) -> None:
        with pytest.raises(ValueError):
            CheckHeatmap(bucket_format="")

    def test_check_names_empty_initially(self) -> None:
        assert self.heatmap.check_names() == []

    def test_record_passed_increments_total_not_failures(self) -> None:
        r = _make_result("db", CheckStatus.PASSED, TS_A)
        self.heatmap.record(r)
        cell = self.heatmap.get("db", "2024-06-01T09")
        assert cell is not None
        assert cell.total_count == 1
        assert cell.failure_count == 0

    def test_record_failed_increments_both(self) -> None:
        r = _make_result("db", CheckStatus.FAILED, TS_A)
        self.heatmap.record(r)
        cell = self.heatmap.get("db", "2024-06-01T09")
        assert cell is not None
        assert cell.total_count == 1
        assert cell.failure_count == 1

    def test_record_error_counts_as_failure(self) -> None:
        r = _make_result("db", CheckStatus.ERROR, TS_A)
        self.heatmap.record(r)
        cell = self.heatmap.get("db", "2024-06-01T09")
        assert cell.failure_count == 1

    def test_same_hour_results_aggregated(self) -> None:
        self.heatmap.record(_make_result("db", CheckStatus.FAILED, TS_A))
        self.heatmap.record(_make_result("db", CheckStatus.PASSED, TS_B))
        cell = self.heatmap.get("db", "2024-06-01T09")
        assert cell.total_count == 2
        assert cell.failure_count == 1

    def test_different_hours_separate_cells(self) -> None:
        self.heatmap.record(_make_result("db", CheckStatus.FAILED, TS_A))
        self.heatmap.record(_make_result("db", CheckStatus.FAILED, TS_C))
        assert self.heatmap.get("db", "2024-06-01T09").total_count == 1
        assert self.heatmap.get("db", "2024-06-01T10").total_count == 1

    def test_get_returns_none_for_unknown_check(self) -> None:
        assert self.heatmap.get("missing", "2024-06-01T09") is None

    def test_get_returns_none_for_unknown_bucket(self) -> None:
        self.heatmap.record(_make_result("db", CheckStatus.PASSED, TS_A))
        assert self.heatmap.get("db", "2099-01-01T00") is None

    def test_failure_rate_calculation(self) -> None:
        self.heatmap.record(_make_result("db", CheckStatus.FAILED, TS_A))
        self.heatmap.record(_make_result("db", CheckStatus.PASSED, TS_B))
        cell = self.heatmap.get("db", "2024-06-01T09")
        assert cell.failure_rate == pytest.approx(0.5)

    def test_failure_rate_zero_when_no_runs(self) -> None:
        cell = HeatmapCell(check_name="x", bucket="b", failure_count=0, total_count=0)
        assert cell.failure_rate == 0.0

    def test_hottest_returns_top_n(self) -> None:
        self.heatmap.record(_make_result("a", CheckStatus.FAILED, TS_A))
        self.heatmap.record(_make_result("a", CheckStatus.FAILED, TS_B))
        self.heatmap.record(_make_result("b", CheckStatus.FAILED, TS_A))
        top = self.heatmap.hottest(top_n=1)
        assert len(top) == 1
        assert top[0].check_name == "a"

    def test_check_names_sorted(self) -> None:
        self.heatmap.record(_make_result("z", CheckStatus.PASSED, TS_A))
        self.heatmap.record(_make_result("a", CheckStatus.PASSED, TS_A))
        assert self.heatmap.check_names() == ["a", "z"]

    def test_buckets_for_sorted(self) -> None:
        self.heatmap.record(_make_result("db", CheckStatus.PASSED, TS_C))
        self.heatmap.record(_make_result("db", CheckStatus.PASSED, TS_A))
        buckets = self.heatmap.buckets_for("db")
        assert buckets == sorted(buckets)


class TestHeatmapReporter:
    def test_raises_on_non_heatmap(self) -> None:
        with pytest.raises(TypeError):
            HeatmapReporter("not a heatmap")  # type: ignore

    def test_render_empty_message_when_no_data(self) -> None:
        reporter = HeatmapReporter(CheckHeatmap())
        output = reporter.render()
        assert "no data" in output

    def test_render_contains_check_name(self) -> None:
        heatmap = CheckHeatmap()
        heatmap.record(_make_result("my_check", CheckStatus.FAILED, TS_A))
        reporter = HeatmapReporter(heatmap)
        assert "my_check" in reporter.render()

    def test_render_contains_bucket(self) -> None:
        heatmap = CheckHeatmap()
        heatmap.record(_make_result("db", CheckStatus.PASSED, TS_A))
        reporter = HeatmapReporter(heatmap)
        assert "2024-06-01T09" in reporter.render()

    def test_render_contains_percentage(self) -> None:
        heatmap = CheckHeatmap()
        heatmap.record(_make_result("db", CheckStatus.FAILED, TS_A))
        reporter = HeatmapReporter(heatmap)
        assert "%" in reporter.render()

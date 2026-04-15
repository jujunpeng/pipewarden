"""Tests for pipewarden.snapshot_builder."""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.pipeline import PipelineReport
from pipewarden.snapshot import PipelineSnapshot, SnapshotStore
from pipewarden.snapshot_builder import SnapshotBuilder


def _make_result(name: str, status: CheckStatus = CheckStatus.PASSED) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="ok", duration_ms=1.0)


def _make_report(*names: str) -> PipelineReport:
    checks = [MagicMock(name=n) for n in names]
    results = [_make_result(n) for n in names]
    return PipelineReport(checks=checks, results=results)


class TestSnapshotBuilder:
    def test_build_returns_snapshot(self):
        builder = SnapshotBuilder()
        report = _make_report("c1", "c2")
        snap = builder.build(report)
        assert isinstance(snap, PipelineSnapshot)

    def test_build_copies_results(self):
        builder = SnapshotBuilder()
        report = _make_report("c1", "c2")
        snap = builder.build(report)
        assert len(snap.results) == 2

    def test_build_uses_provided_label(self):
        builder = SnapshotBuilder()
        snap = builder.build(_make_report("c1"), label="prod")
        assert snap.label == "prod"

    def test_build_uses_provided_timestamp(self):
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        builder = SnapshotBuilder()
        snap = builder.build(_make_report("c1"), taken_at=ts)
        assert snap.taken_at == ts

    def test_build_sets_timestamp_when_not_provided(self):
        builder = SnapshotBuilder()
        snap = builder.build(_make_report("c1"))
        assert snap.taken_at is not None

    def test_build_saves_to_store_when_provided(self):
        store = SnapshotStore()
        builder = SnapshotBuilder(store=store)
        builder.build(_make_report("c1"))
        assert len(store) == 1

    def test_build_does_not_save_without_store(self):
        builder = SnapshotBuilder()
        snap = builder.build(_make_report("c1"))
        assert snap is not None  # no error

    def test_store_property(self):
        store = SnapshotStore()
        builder = SnapshotBuilder(store=store)
        assert builder.store is store

    def test_store_property_none_by_default(self):
        builder = SnapshotBuilder()
        assert builder.store is None

    def test_latest_returns_none_without_store(self):
        builder = SnapshotBuilder()
        assert builder.latest() is None

    def test_latest_returns_most_recent_snapshot(self):
        store = SnapshotStore()
        builder = SnapshotBuilder(store=store)
        builder.build(_make_report("c1"), label="first")
        builder.build(_make_report("c2"), label="second")
        latest = builder.latest()
        assert latest is not None
        assert latest.label == "second"

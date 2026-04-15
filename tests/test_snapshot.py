"""Tests for pipewarden.snapshot."""
from datetime import datetime, timezone

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.snapshot import PipelineSnapshot, SnapshotStore


def _make_result(name: str, status: CheckStatus, duration: float = 0.1) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="ok",
        duration_ms=duration,
    )


def _make_snapshot(
    results=None, label: str = "test", ts: datetime = None
) -> PipelineSnapshot:
    if results is None:
        results = [_make_result("c1", CheckStatus.PASSED)]
    if ts is None:
        ts = datetime.now(timezone.utc)
    return PipelineSnapshot(taken_at=ts, results=results, label=label)


class TestPipelineSnapshot:
    def test_passed_when_all_pass(self):
        snap = _make_snapshot([_make_result("a", CheckStatus.PASSED)])
        assert snap.passed() is True

    def test_not_passed_when_any_failed(self):
        snap = _make_snapshot(
            [
                _make_result("a", CheckStatus.PASSED),
                _make_result("b", CheckStatus.FAILED),
            ]
        )
        assert snap.passed() is False

    def test_summary_counts(self):
        snap = _make_snapshot(
            [
                _make_result("a", CheckStatus.PASSED),
                _make_result("b", CheckStatus.FAILED),
                _make_result("c", CheckStatus.ERROR),
            ]
        )
        s = snap.summary()
        assert s["passed"] == 1
        assert s["failed"] == 1
        assert s["error"] == 1

    def test_find_returns_result(self):
        r = _make_result("my_check", CheckStatus.PASSED)
        snap = _make_snapshot([r])
        found = snap.find("my_check")
        assert found is r

    def test_find_returns_none_for_missing(self):
        snap = _make_snapshot()
        assert snap.find("nonexistent") is None


class TestSnapshotStore:
    def setup_method(self):
        self.store = SnapshotStore(max_snapshots=3)

    def test_raises_on_zero_max(self):
        with pytest.raises(ValueError):
            SnapshotStore(max_snapshots=0)

    def test_raises_on_negative_max(self):
        with pytest.raises(ValueError):
            SnapshotStore(max_snapshots=-1)

    def test_max_snapshots_property(self):
        assert self.store.max_snapshots == 3

    def test_latest_none_when_empty(self):
        assert self.store.latest() is None

    def test_save_and_latest(self):
        snap = _make_snapshot()
        self.store.save(snap)
        assert self.store.latest() is snap

    def test_len(self):
        self.store.save(_make_snapshot())
        self.store.save(_make_snapshot())
        assert len(self.store) == 2

    def test_evicts_oldest_when_over_cap(self):
        snaps = [_make_snapshot(label=str(i)) for i in range(4)]
        for s in snaps:
            self.store.save(s)
        assert len(self.store) == 3
        assert self.store.all()[0].label == "1"

    def test_all_returns_copy(self):
        snap = _make_snapshot()
        self.store.save(snap)
        lst = self.store.all()
        lst.clear()
        assert len(self.store) == 1

    def test_diff_none_when_fewer_than_two(self):
        self.store.save(_make_snapshot())
        assert self.store.diff() is None

    def test_diff_detects_status_change(self):
        r1 = _make_result("c", CheckStatus.PASSED)
        r2 = _make_result("c", CheckStatus.FAILED)
        self.store.save(_make_snapshot([r1]))
        self.store.save(_make_snapshot([r2]))
        diff = self.store.diff()
        assert diff is not None
        assert "c" in diff["changed"]
        assert diff["changed"]["c"]["before"] == "passed"
        assert diff["changed"]["c"]["after"] == "failed"

    def test_diff_detects_added_check(self):
        self.store.save(_make_snapshot([_make_result("a", CheckStatus.PASSED)]))
        self.store.save(
            _make_snapshot(
                [
                    _make_result("a", CheckStatus.PASSED),
                    _make_result("b", CheckStatus.PASSED),
                ]
            )
        )
        diff = self.store.diff()
        assert "b" in diff["added"]

    def test_diff_detects_removed_check(self):
        self.store.save(
            _make_snapshot(
                [
                    _make_result("a", CheckStatus.PASSED),
                    _make_result("b", CheckStatus.PASSED),
                ]
            )
        )
        self.store.save(_make_snapshot([_make_result("a", CheckStatus.PASSED)]))
        diff = self.store.diff()
        assert "b" in diff["removed"]

"""Tests for pipewarden.digest and pipewarden.digest_sender."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.digest import DigestEntry, PipelineDigest
from pipewarden.digest_sender import DigestSender
from pipewarden.snapshot import PipelineSnapshot


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="", duration_ms=1.0)


def _make_snapshot(all_pass: bool) -> PipelineSnapshot:
    status = CheckStatus.PASSED if all_pass else CheckStatus.FAILED
    results = [_make_result("c1", status)]
    return PipelineSnapshot(results=results, taken_at=datetime.utcnow())


# ---------------------------------------------------------------------------
# DigestEntry
# ---------------------------------------------------------------------------

class TestDigestEntry:
    def test_snapshot_stored(self):
        snap = _make_snapshot(True)
        entry = DigestEntry(snapshot=snap)
        assert entry.snapshot is snap

    def test_recorded_at_auto_set(self):
        entry = DigestEntry(snapshot=_make_snapshot(True))
        assert isinstance(entry.recorded_at, datetime)


# ---------------------------------------------------------------------------
# PipelineDigest
# ---------------------------------------------------------------------------

class TestPipelineDigest:
    def setup_method(self):
        self.digest = PipelineDigest(title="Test Digest")

    def test_title_stored(self):
        assert self.digest.title == "Test Digest"

    def test_raises_on_empty_title(self):
        with pytest.raises(ValueError):
            PipelineDigest(title="")

    def test_raises_on_blank_title(self):
        with pytest.raises(ValueError):
            PipelineDigest(title="   ")

    def test_initial_entry_count_zero(self):
        assert self.digest.entry_count == 0

    def test_add_increments_count(self):
        self.digest.add(_make_snapshot(True))
        assert self.digest.entry_count == 1

    def test_add_multiple_increments_count(self):
        for i in range(5):
            self.digest.add(_make_snapshot(i % 2 == 0))
        assert self.digest.entry_count == 5

    def test_clear_resets_count(self):
        self.digest.add(_make_snapshot(True))
        self.digest.clear()
        assert self.digest.entry_count == 0

    def test_clear_allows_readding(self):
        self.digest.add(_make_snapshot(True))
        self.digest.clear()
        self.digest.add(_make_snapshot(False))
        assert self.digest.entry_count == 1

    def test_pass_rate_zero_when_empty(self):
        assert self.digest.overall_pass_rate() == 0.0

    def test_pass_rate_all_pass(self):
        for _ in range(4):
            self.digest.add(_make_snapshot(True))
        assert self.digest.overall_pass_rate() == 1.0

    def test_pass_rate_all_fail(self):
        for _ in range(3):
            self.digest.add(_make_snapshot(False))
        assert self.digest.overall_pass_rate() == 0.0

    def test_pass_rate_mixed(self):
        self.digest.add(_make_snapshot(True))
        self.digest.add(_make_snapshot(False))
        assert self.digest.overall_pass_rate() == 0.5

    def test_render_contains_title(self):
        rendered = self.digest.render()

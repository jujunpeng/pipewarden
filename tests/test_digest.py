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

    def test_clear_resets_count(self):
        self.digest.add(_make_snapshot(True))
        self.digest.clear()
        assert self.digest.entry_count == 0

    def test_pass_rate_zero_when_empty(self):
        assert self.digest.overall_pass_rate() == 0.0

    def test_pass_rate_all_pass(self):
        for _ in range(4):
            self.digest.add(_make_snapshot(True))
        assert self.digest.overall_pass_rate() == 1.0

    def test_pass_rate_mixed(self):
        self.digest.add(_make_snapshot(True))
        self.digest.add(_make_snapshot(False))
        assert self.digest.overall_pass_rate() == 0.5

    def test_render_contains_title(self):
        rendered = self.digest.render()
        assert "Test Digest" in rendered

    def test_render_contains_pass_rate(self):
        self.digest.add(_make_snapshot(True))
        rendered = self.digest.render()
        assert "100%" in rendered

    def test_render_contains_snapshot_status(self):
        self.digest.add(_make_snapshot(False))
        rendered = self.digest.render()
        assert "FAIL" in rendered


# ---------------------------------------------------------------------------
# DigestSender
# ---------------------------------------------------------------------------

class TestDigestSender:
    def setup_method(self):
        self.handler = MagicMock()
        self.sender = DigestSender(handlers=[self.handler])
        self.digest = PipelineDigest(title="Sender Test")
        self.digest.add(_make_snapshot(False))

    def test_handler_count(self):
        assert self.sender.handler_count == 1

    def test_add_handler_increments_count(self):
        self.sender.add_handler(MagicMock())
        assert self.sender.handler_count == 2

    def test_send_calls_handler(self):
        self.sender.send(self.digest)
        self.handler.send.assert_called_once()

    def test_send_passes_check_result(self):
        self.sender.send(self.digest)
        args, _ = self.handler.send.call_args
        assert isinstance(args[0], CheckResult)

    def test_send_message_contains_digest_text(self):
        self.sender.send(self.digest)
        args, _ = self.handler.send.call_args
        result: CheckResult = args[0]
        assert "Sender Test" in result.message

    def test_send_no_handlers_does_not_raise(self):
        sender = DigestSender()
        sender.send(self.digest)  # should not raise

    def test_send_multiple_handlers(self):
        h2 = MagicMock()
        self.sender.add_handler(h2)
        self.sender.send(self.digest)
        self.handler.send.assert_called_once()
        h2.send.assert_called_once()

"""Tests for pipewarden.sink."""
import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.sink import ResultSink


def _make_result(name: str = "check", status: CheckStatus = CheckStatus.PASSED) -> CheckResult:
    return CheckResult(check_name=name, status=status)


class TestResultSink:
    def setup_method(self):
        self.received: list = []
        self.sink = ResultSink(batch_size=3, on_flush=self.received.append)

    def test_raises_on_zero_batch_size(self):
        with pytest.raises(ValueError):
            ResultSink(batch_size=0, on_flush=lambda b: None)

    def test_raises_on_negative_batch_size(self):
        with pytest.raises(ValueError):
            ResultSink(batch_size=-1, on_flush=lambda b: None)

    def test_batch_size_stored(self):
        assert self.sink.batch_size == 3

    def test_initial_pending_is_zero(self):
        assert self.sink.pending == 0

    def test_initial_total_flushed_is_zero(self):
        assert self.sink.total_flushed == 0

    def test_write_increments_pending(self):
        self.sink.write(_make_result())
        assert self.sink.pending == 1

    def test_no_flush_before_batch_full(self):
        self.sink.write(_make_result())
        self.sink.write(_make_result())
        assert len(self.received) == 0

    def test_flush_triggered_when_batch_full(self):
        for _ in range(3):
            self.sink.write(_make_result())
        assert len(self.received) == 1

    def test_pending_resets_after_auto_flush(self):
        for _ in range(3):
            self.sink.write(_make_result())
        assert self.sink.pending == 0

    def test_total_flushed_updated_after_auto_flush(self):
        for _ in range(3):
            self.sink.write(_make_result())
        assert self.sink.total_flushed == 3

    def test_manual_flush_sends_pending(self):
        self.sink.write(_make_result())
        self.sink.flush()
        assert len(self.received) == 1
        assert self.sink.pending == 0

    def test_flush_empty_buffer_is_noop(self):
        self.sink.flush()
        assert len(self.received) == 0

    def test_batch_contains_correct_results(self):
        results = [_make_result(f"c{i}") for i in range(3)]
        for r in results:
            self.sink.write(r)
        flushed_batch = self.received[0]
        assert [r.check_name for r in flushed_batch] == ["c0", "c1", "c2"]

    def test_reset_clears_buffer_without_flush(self):
        self.sink.write(_make_result())
        self.sink.reset()
        assert self.sink.pending == 0
        assert len(self.received) == 0

    def test_multiple_batches_accumulate_total(self):
        for _ in range(6):
            self.sink.write(_make_result())
        assert self.sink.total_flushed == 6
        assert len(self.received) == 2

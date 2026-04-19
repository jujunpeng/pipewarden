"""Tests for pipewarden.replay."""
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.alerts import AlertHandler
from pipewarden.replay import ReplayFilter, ResultReplayer


def _make_result(name: str = "check", status: CheckStatus = CheckStatus.PASSED) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="ok",
        duration_ms=10.0,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


class _FakeHandler(AlertHandler):
    def __init__(self):
        self.received = []

    def send(self, result: CheckResult) -> None:
        self.received.append(result)


class TestReplayFilter:
    def test_matches_true(self):
        f = ReplayFilter(predicate=lambda r: r.status == CheckStatus.PASSED)
        assert f.matches(_make_result(status=CheckStatus.PASSED)) is True

    def test_matches_false(self):
        f = ReplayFilter(predicate=lambda r: r.status == CheckStatus.FAILED)
        assert f.matches(_make_result(status=CheckStatus.PASSED)) is False

    def test_matches_returns_false_on_exception(self):
        f = ReplayFilter(predicate=lambda r: 1 / 0)
        assert f.matches(_make_result()) is False

    def test_repr_contains_filter(self):
        pred = lambda r: True
        f = ReplayFilter(predicate=pred)
        assert "ReplayFilter" in repr(f)


class TestResultReplayer:
    def setup_method(self):
        self.replayer = ResultReplayer()
        self.handler = _FakeHandler()
        self.replayer.add_handler(self.handler)

    def test_initial_counts_zero(self):
        assert self.replayer.replayed_count == 0
        assert self.replayer.skipped_count == 0

    def test_handler_count(self):
        assert self.replayer.handler_count == 1

    def test_add_invalid_handler_raises(self):
        with pytest.raises(TypeError):
            self.replayer.add_handler(object())

    def test_replay_sends_to_handler(self):
        results = [_make_result("a"), _make_result("b")]
        count = self.replayer.replay(results)
        assert count == 2
        assert len(self.handler.received) == 2

    def test_replay_increments_replayed_count(self):
        self.replayer.replay([_make_result(), _make_result()])
        assert self.replayer.replayed_count == 2

    def test_replay_with_filter_skips_non_matching(self):
        results = [
            _make_result("a", CheckStatus.PASSED),
            _make_result("b", CheckStatus.FAILED),
        ]
        f = ReplayFilter(predicate=lambda r: r.status == CheckStatus.FAILED)
        count = self.replayer.replay(results, replay_filter=f)
        assert count == 1
        assert self.replayer.skipped_count == 1
        assert len(self.handler.received) == 1

    def test_reset_clears_counts(self):
        self.replayer.replay([_make_result()])
        self.replayer.reset()
        assert self.replayer.replayed_count == 0
        assert self.replayer.skipped_count == 0

    def test_repr_contains_class_name(self):
        assert "ResultReplayer" in repr(self.replayer)

    def test_multiple_handlers_all_receive(self):
        h2 = _FakeHandler()
        self.replayer.add_handler(h2)
        self.replayer.replay([_make_result()])
        assert len(self.handler.received) == 1
        assert len(h2.received) == 1

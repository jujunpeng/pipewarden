"""Tests for pipewarden.event_log."""
from datetime import datetime, timezone

import pytest

from pipewarden.event_log import EventKind, EventLog, PipelineEvent


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_event(
    kind: EventKind = EventKind.CHECK_PASSED,
    check_name: str | None = "my_check",
    message: str = "ok",
) -> PipelineEvent:
    return PipelineEvent(kind=kind, check_name=check_name, message=message)


# ---------------------------------------------------------------------------
# PipelineEvent
# ---------------------------------------------------------------------------

class TestPipelineEvent:
    def test_fields_stored(self):
        evt = _make_event()
        assert evt.kind == EventKind.CHECK_PASSED
        assert evt.check_name == "my_check"
        assert evt.message == "ok"

    def test_recorded_at_auto_set(self):
        evt = _make_event()
        assert isinstance(evt.recorded_at, datetime)
        assert evt.recorded_at.tzinfo is not None

    def test_is_frozen(self):
        evt = _make_event()
        with pytest.raises((AttributeError, TypeError)):
            evt.message = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# EventLog
# ---------------------------------------------------------------------------

class TestEventLog:
    def setup_method(self):
        self.log = EventLog()

    def test_default_max_size(self):
        assert self.log.max_size == EventLog.DEFAULT_MAX_SIZE

    def test_custom_max_size(self):
        log = EventLog(max_size=10)
        assert log.max_size == 10

    def test_raises_on_zero_max_size(self):
        with pytest.raises(ValueError):
            EventLog(max_size=0)

    def test_raises_on_negative_max_size(self):
        with pytest.raises(ValueError):
            EventLog(max_size=-1)

    def test_initial_len_is_zero(self):
        assert len(self.log) == 0

    def test_record_increments_len(self):
        self.log.record(_make_event())
        assert len(self.log) == 1

    def test_raises_on_non_event(self):
        with pytest.raises(TypeError):
            self.log.record("not an event")  # type: ignore[arg-type]

    def test_all_returns_list(self):
        self.log.record(_make_event())
        result = self.log.all()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_all_returns_copy(self):
        self.log.record(_make_event())
        result = self.log.all()
        result.clear()
        assert len(self.log) == 1

    def test_by_kind_filters_correctly(self):
        self.log.record(_make_event(kind=EventKind.CHECK_PASSED))
        self.log.record(_make_event(kind=EventKind.CHECK_FAILED))
        self.log.record(_make_event(kind=EventKind.CHECK_PASSED))
        passed = self.log.by_kind(EventKind.CHECK_PASSED)
        assert len(passed) == 2
        assert all(e.kind == EventKind.CHECK_PASSED for e in passed)

    def test_by_check_filters_correctly(self):
        self.log.record(_make_event(check_name="alpha"))
        self.log.record(_make_event(check_name="beta"))
        self.log.record(_make_event(check_name="alpha"))
        result = self.log.by_check("alpha")
        assert len(result) == 2
        assert all(e.check_name == "alpha" for e in result)

    def test_by_check_no_match_returns_empty(self):
        self.log.record(_make_event(check_name="alpha"))
        assert self.log.by_check("unknown") == []

    def test_capacity_drops_oldest(self):
        log = EventLog(max_size=3)
        for i in range(5):
            log.record(_make_event(message=str(i)))
        assert len(log) == 3
        messages = [e.message for e in log.all()]
        assert messages == ["2", "3", "4"]

    def test_clear_empties_log(self):
        self.log.record(_make_event())
        self.log.clear()
        assert len(self.log) == 0

    def test_iter_yields_events(self):
        self.log.record(_make_event(message="a"))
        self.log.record(_make_event(message="b"))
        messages = [e.message for e in self.log]
        assert messages == ["a", "b"]

    def test_pipeline_event_without_check_name(self):
        evt = PipelineEvent(
            kind=EventKind.PIPELINE_STARTED,
            check_name=None,
            message="pipeline started",
        )
        self.log.record(evt)
        result = self.log.by_kind(EventKind.PIPELINE_STARTED)
        assert len(result) == 1
        assert result[0].check_name is None

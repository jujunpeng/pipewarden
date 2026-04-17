"""Tests for pipewarden.audit."""
import pytest
from pipewarden.audit import AuditLog, AuditEntry
from pipewarden.checks import CheckResult, CheckStatus
from datetime import datetime


def _make_result(name: str, status: CheckStatus, msg: str = "ok", dur: float = 10.0) -> CheckResult:
    return CheckResult(check_name=name, status=status, message=msg, duration_ms=dur)


class TestAuditLog:
    def setup_method(self):
        self.log = AuditLog()

    def test_default_max_size(self):
        assert self.log.max_size == 500

    def test_custom_max_size(self):
        log = AuditLog(max_size=10)
        assert log.max_size == 10

    def test_raises_on_zero_max_size(self):
        with pytest.raises(ValueError):
            AuditLog(max_size=0)

    def test_raises_on_negative_max_size(self):
        with pytest.raises(ValueError):
            AuditLog(max_size=-1)

    def test_initial_len_zero(self):
        assert len(self.log) == 0

    def test_record_increments_len(self):
        self.log.record(_make_result("check_a", CheckStatus.PASSED))
        assert len(self.log) == 1

    def test_all_returns_copy(self):
        self.log.record(_make_result("check_a", CheckStatus.PASSED))
        entries = self.log.all()
        entries.clear()
        assert len(self.log) == 1

    def test_entry_fields_match_result(self):
        result = _make_result("check_x", CheckStatus.FAILED, "bad", 42.5)
        self.log.record(result)
        entry = self.log.all()[0]
        assert entry.check_name == "check_x"
        assert entry.status == CheckStatus.FAILED
        assert entry.message == "bad"
        assert entry.duration_ms == 42.5

    def test_recorded_at_is_datetime(self):
        self.log.record(_make_result("c", CheckStatus.PASSED))
        assert isinstance(self.log.all()[0].recorded_at, datetime)

    def test_for_check_filters_by_name(self):
        self.log.record(_make_result("a", CheckStatus.PASSED))
        self.log.record(_make_result("b", CheckStatus.FAILED))
        self.log.record(_make_result("a", CheckStatus.FAILED))
        assert len(self.log.for_check("a")) == 2
        assert len(self.log.for_check("b")) == 1

    def test_failures_excludes_passed(self):
        self.log.record(_make_result("a", CheckStatus.PASSED))
        self.log.record(_make_result("b", CheckStatus.FAILED))
        self.log.record(_make_result("c", CheckStatus.ERROR))
        failures = self.log.failures()
        assert len(failures) == 2
        assert all(e.status != CheckStatus.PASSED for e in failures)

    def test_evicts_oldest_when_full(self):
        log = AuditLog(max_size=3)
        for i in range(4):
            log.record(_make_result(f"check_{i}", CheckStatus.PASSED))
        assert len(log) == 3
        assert log.all()[0].check_name == "check_1"

    def test_clear_empties_log(self):
        self.log.record(_make_result("a", CheckStatus.PASSED))
        self.log.clear()
        assert len(self.log) == 0

    def test_repr_entry(self):
        self.log.record(_make_result("z", CheckStatus.PASSED))
        r = repr(self.log.all()[0])
        assert "z" in r
        assert "passed" in r

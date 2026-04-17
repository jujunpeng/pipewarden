"""Tests for pipewarden.deduplicator."""
import pytest
from datetime import datetime
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.deduplicator import Deduplicator


def _make_result(name: str, status: CheckStatus, duration_ms: float = 10.0) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="msg",
        duration_ms=duration_ms,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


class TestDeduplicator:
    def setup_method(self):
        self.dedup = Deduplicator()

    def test_first_result_is_not_duplicate(self):
        r = _make_result("check_a", CheckStatus.PASSED)
        assert self.dedup.is_duplicate(r) is False

    def test_same_status_is_duplicate(self):
        r = _make_result("check_a", CheckStatus.FAILED)
        self.dedup.is_duplicate(r)
        assert self.dedup.is_duplicate(r) is True

    def test_different_status_not_duplicate(self):
        r1 = _make_result("check_a", CheckStatus.PASSED)
        r2 = _make_result("check_a", CheckStatus.FAILED)
        self.dedup.is_duplicate(r1)
        assert self.dedup.is_duplicate(r2) is False

    def test_suppressed_count_increments(self):
        r = _make_result("check_a", CheckStatus.FAILED)
        self.dedup.is_duplicate(r)
        self.dedup.is_duplicate(r)
        self.dedup.is_duplicate(r)
        assert self.dedup.suppressed_count("check_a") == 2

    def test_suppressed_count_zero_for_unknown(self):
        assert self.dedup.suppressed_count("nonexistent") == 0

    def test_reset_single_check(self):
        r = _make_result("check_a", CheckStatus.FAILED)
        self.dedup.is_duplicate(r)
        self.dedup.is_duplicate(r)
        self.dedup.reset("check_a")
        assert self.dedup.suppressed_count("check_a") == 0
        assert "check_a" not in self.dedup.known_checks()

    def test_reset_all_checks(self):
        for name in ("a", "b", "c"):
            r = _make_result(name, CheckStatus.PASSED)
            self.dedup.is_duplicate(r)
        self.dedup.reset()
        assert self.dedup.known_checks() == []

    def test_known_checks_returns_tracked_names(self):
        self.dedup.is_duplicate(_make_result("x", CheckStatus.PASSED))
        self.dedup.is_duplicate(_make_result("y", CheckStatus.FAILED))
        assert set(self.dedup.known_checks()) == {"x", "y"}

    def test_record_does_not_increment_suppressed(self):
        r = _make_result("check_b", CheckStatus.PASSED)
        self.dedup.record(r)
        self.dedup.record(r)
        assert self.dedup.suppressed_count("check_b") == 0

    def test_record_then_is_duplicate(self):
        r = _make_result("check_b", CheckStatus.ERROR)
        self.dedup.record(r)
        assert self.dedup.is_duplicate(r) is True

    def test_independent_checks_do_not_interfere(self):
        ra = _make_result("a", CheckStatus.PASSED)
        rb = _make_result("b", CheckStatus.FAILED)
        self.dedup.is_duplicate(ra)
        self.dedup.is_duplicate(rb)
        assert self.dedup.is_duplicate(ra) is True
        assert self.dedup.suppressed_count("b") == 0

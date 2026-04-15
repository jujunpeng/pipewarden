"""Tests for pipewarden.watchdog."""

from datetime import datetime, timedelta

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.watchdog import CheckWatchdog, StalenessViolation


def _make_result(name: str, ts: datetime) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=CheckStatus.PASSED,
        message="ok",
        timestamp=ts,
        duration_ms=10.0,
    )


NOW = datetime(2024, 6, 1, 12, 0, 0)


class TestCheckWatchdog:
    def setup_method(self):
        self.dog = CheckWatchdog(max_age_seconds=60.0)

    def test_raises_on_zero_max_age(self):
        with pytest.raises(ValueError):
            CheckWatchdog(max_age_seconds=0)

    def test_raises_on_negative_max_age(self):
        with pytest.raises(ValueError):
            CheckWatchdog(max_age_seconds=-1)

    def test_max_age_stored(self):
        assert self.dog.max_age_seconds == 60.0

    def test_no_known_checks_initially(self):
        assert self.dog.known_checks() == []

    def test_record_adds_check(self):
        result = _make_result("db_check", NOW)
        self.dog.record(result)
        assert "db_check" in self.dog.known_checks()

    def test_record_many_adds_all(self):
        results = [
            _make_result("a", NOW),
            _make_result("b", NOW),
        ]
        self.dog.record_many(results)
        assert set(self.dog.known_checks()) == {"a", "b"}

    def test_is_stale_unknown_check(self):
        assert self.dog.is_stale("unknown", now=NOW) is True

    def test_is_not_stale_when_recent(self):
        result = _make_result("fresh", NOW)
        self.dog.record(result)
        later = NOW + timedelta(seconds=30)
        assert self.dog.is_stale("fresh", now=later) is False

    def test_is_stale_when_overdue(self):
        result = _make_result("old", NOW)
        self.dog.record(result)
        later = NOW + timedelta(seconds=120)
        assert self.dog.is_stale("old", now=later) is True

    def test_is_stale_exactly_at_boundary(self):
        result = _make_result("edge", NOW)
        self.dog.record(result)
        at_limit = NOW + timedelta(seconds=60)
        # strictly greater than, so exactly at boundary is NOT stale
        assert self.dog.is_stale("edge", now=at_limit) is False

    def test_violations_empty_when_all_fresh(self):
        self.dog.record(_make_result("x", NOW))
        later = NOW + timedelta(seconds=10)
        assert self.dog.violations(now=later) == []

    def test_violations_returns_stale_checks(self):
        self.dog.record(_make_result("stale_check", NOW))
        later = NOW + timedelta(seconds=200)
        viols = self.dog.violations(now=later)
        assert len(viols) == 1
        assert viols[0].check_name == "stale_check"

    def test_violations_only_includes_stale(self):
        self.dog.record(_make_result("fresh", NOW))
        self.dog.record(_make_result("stale", NOW - timedelta(seconds=120)))
        viols = self.dog.violations(now=NOW)
        names = [v.check_name for v in viols]
        assert "stale" in names
        assert "fresh" not in names

    def test_staleness_violation_repr(self):
        v = StalenessViolation(
            check_name="my_check",
            last_seen=NOW,
            max_age_seconds=60.0,
            detected_at=NOW,
        )
        assert "my_check" in repr(v)
        assert "60.0" in repr(v)

    def test_staleness_violation_repr_never_seen(self):
        v = StalenessViolation(
            check_name="ghost",
            last_seen=None,
            max_age_seconds=30.0,
            detected_at=NOW,
        )
        assert "never" in repr(v)

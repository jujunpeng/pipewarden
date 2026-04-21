"""Tests for pipewarden.quota (CheckQuota and QuotaViolation)."""
from __future__ import annotations

import time

import pytest

from pipewarden.quota import CheckQuota, QuotaViolation


class TestCheckQuota:
    def setup_method(self):
        self.quota = CheckQuota("row_count", limit=3, window_seconds=10.0)

    def test_raises_on_zero_limit(self):
        with pytest.raises(ValueError, match="limit"):
            CheckQuota("x", limit=0, window_seconds=10.0)

    def test_raises_on_negative_limit(self):
        with pytest.raises(ValueError, match="limit"):
            CheckQuota("x", limit=-1, window_seconds=10.0)

    def test_raises_on_zero_window(self):
        with pytest.raises(ValueError, match="window_seconds"):
            CheckQuota("x", limit=5, window_seconds=0.0)

    def test_raises_on_negative_window(self):
        with pytest.raises(ValueError, match="window_seconds"):
            CheckQuota("x", limit=5, window_seconds=-1.0)

    def test_check_name_stored(self):
        assert self.quota.check_name == "row_count"

    def test_limit_stored(self):
        assert self.quota.limit == 3

    def test_window_seconds_stored(self):
        assert self.quota.window_seconds == 10.0

    def test_allowed_before_any_record(self):
        now = time.time()
        assert self.quota.is_allowed(now) is True

    def test_allowed_up_to_limit(self):
        now = time.time()
        for _ in range(3):
            assert self.quota.is_allowed(now) is True
            self.quota.record(now)

    def test_not_allowed_after_limit_reached(self):
        now = time.time()
        for _ in range(3):
            self.quota.record(now)
        assert self.quota.is_allowed(now) is False

    def test_allowed_again_after_window_expires(self):
        now = time.time()
        for _ in range(3):
            self.quota.record(now)
        future = now + 11.0
        assert self.quota.is_allowed(future) is True

    def test_current_count_reflects_records(self):
        now = time.time()
        self.quota.record(now)
        self.quota.record(now)
        assert self.quota.current_count(now) == 2

    def test_current_count_evicts_old_records(self):
        now = time.time()
        self.quota.record(now)
        future = now + 20.0
        assert self.quota.current_count(future) == 0

    def test_violation_contains_check_name(self):
        v = self.quota.violation()
        assert v.check_name == "row_count"

    def test_violation_contains_limit(self):
        v = self.quota.violation()
        assert v.limit == 3

    def test_repr_contains_check_name(self):
        assert "row_count" in repr(self.quota)

    def test_repr_contains_limit(self):
        assert "3" in repr(self.quota)


class TestQuotaViolation:
    def test_repr_contains_check_name(self):
        v = QuotaViolation(check_name="nulls", limit=5, window_seconds=30.0)
        assert "nulls" in repr(v)

    def test_repr_contains_limit(self):
        v = QuotaViolation(check_name="nulls", limit=5, window_seconds=30.0)
        assert "5" in repr(v)

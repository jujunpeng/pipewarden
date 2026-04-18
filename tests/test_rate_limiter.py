"""Tests for pipewarden.rate_limiter."""

import time

import pytest

from pipewarden.rate_limiter import RateLimiter


class TestRateLimiter:
    def setup_method(self):
        self.limiter = RateLimiter(min_interval_seconds=1.0)

    # --- construction ---

    def test_raises_on_zero_interval(self):
        with pytest.raises(ValueError):
            RateLimiter(min_interval_seconds=0)

    def test_raises_on_negative_interval(self):
        with pytest.raises(ValueError):
            RateLimiter(min_interval_seconds=-5)

    def test_stores_interval(self):
        r = RateLimiter(min_interval_seconds=30)
        assert r.min_interval_seconds == 30

    # --- is_allowed ---

    def test_allowed_before_any_record(self):
        assert self.limiter.is_allowed("check_a") is True

    def test_not_allowed_immediately_after_record(self):
        self.limiter.record("check_a")
        assert self.limiter.is_allowed("check_a") is False

    def test_allowed_after_interval_elapsed(self):
        fast = RateLimiter(min_interval_seconds=0.05)
        fast.record("check_a")
        time.sleep(0.07)
        assert fast.is_allowed("check_a") is True

    def test_different_checks_independent(self):
        self.limiter.record("check_a")
        assert self.limiter.is_allowed("check_b") is True

    # --- seconds_until_allowed ---

    def test_zero_when_never_recorded(self):
        assert self.limiter.seconds_until_allowed("check_x") == 0.0

    def test_positive_immediately_after_record(self):
        self.limiter.record("check_a")
        remaining = self.limiter.seconds_until_allowed("check_a")
        assert 0 < remaining <= 1.0

    def test_zero_after_interval_elapsed(self):
        fast = RateLimiter(min_interval_seconds=0.05)
        fast.record("check_a")
        time.sleep(0.07)
        assert fast.seconds_until_allowed("check_a") == 0.0

    # --- reset ---

    def test_reset_allows_immediate_rerun(self):
        self.limiter.record("check_a")
        self.limiter.reset("check_a")
        assert self.limiter.is_allowed("check_a") is True

    def test_reset_unknown_check_is_safe(self):
        self.limiter.reset("nonexistent")  # should not raise

    # --- reset_all ---

    def test_reset_all_clears_all_checks(self):
        self.limiter.record("check_a")
        self.limiter.record("check_b")
        self.limiter.reset_all()
        assert self.limiter.is_allowed("check_a") is True
        assert self.limiter.is_allowed("check_b") is True

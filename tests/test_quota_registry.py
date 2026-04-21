"""Tests for pipewarden.quota_registry (QuotaRegistry)."""
from __future__ import annotations

import pytest

from pipewarden.quota import CheckQuota
from pipewarden.quota_registry import QuotaRegistry


class TestQuotaRegistry:
    def setup_method(self):
        self.registry = QuotaRegistry(default_limit=10, default_window_seconds=60.0)

    def test_raises_on_zero_default_limit(self):
        with pytest.raises(ValueError, match="default_limit"):
            QuotaRegistry(default_limit=0)

    def test_raises_on_negative_default_limit(self):
        with pytest.raises(ValueError, match="default_limit"):
            QuotaRegistry(default_limit=-1)

    def test_raises_on_zero_default_window(self):
        with pytest.raises(ValueError, match="default_window_seconds"):
            QuotaRegistry(default_window_seconds=0.0)

    def test_default_limit_stored(self):
        assert self.registry.default_limit == 10

    def test_default_window_stored(self):
        assert self.registry.default_window_seconds == 60.0

    def test_is_allowed_before_any_record(self):
        assert self.registry.is_allowed("check_a") is True

    def test_record_and_is_allowed_up_to_limit(self):
        reg = QuotaRegistry(default_limit=2, default_window_seconds=60.0)
        reg.record("x")
        assert reg.is_allowed("x") is True
        reg.record("x")
        assert reg.is_allowed("x") is False

    def test_quota_for_returns_check_quota_instance(self):
        q = self.registry.quota_for("check_b")
        assert isinstance(q, CheckQuota)

    def test_quota_for_uses_default_limit(self):
        q = self.registry.quota_for("check_c")
        assert q.limit == 10

    def test_set_override_changes_limit(self):
        self.registry.set_override("check_d", limit=2, window_seconds=30.0)
        q = self.registry.quota_for("check_d")
        assert q.limit == 2
        assert q.window_seconds == 30.0

    def test_set_override_raises_on_bad_limit(self):
        with pytest.raises(ValueError, match="limit"):
            self.registry.set_override("check_e", limit=0, window_seconds=30.0)

    def test_set_override_raises_on_bad_window(self):
        with pytest.raises(ValueError, match="window_seconds"):
            self.registry.set_override("check_e", limit=5, window_seconds=-1.0)

    def test_remove_override_reverts_to_default(self):
        self.registry.set_override("check_f", limit=1, window_seconds=5.0)
        self.registry.remove_override("check_f")
        q = self.registry.quota_for("check_f")
        assert q.limit == 10

    def test_violation_returns_quota_violation(self):
        from pipewarden.quota import QuotaViolation
        v = self.registry.violation("check_g")
        assert isinstance(v, QuotaViolation)
        assert v.check_name == "check_g"

    def test_independent_quotas_per_check(self):
        reg = QuotaRegistry(default_limit=1, default_window_seconds=60.0)
        reg.record("a")
        assert reg.is_allowed("a") is False
        assert reg.is_allowed("b") is True

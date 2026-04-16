"""Tests for CooldownRegistry."""

from datetime import datetime, timedelta

import pytest

from pipewarden.cooldown_registry import CooldownRegistry


class TestCooldownRegistry:
    def setup_method(self):
        self.reg = CooldownRegistry(default_cooldown_seconds=60.0)

    def test_default_cooldown_stored(self):
        assert self.reg.default_cooldown_seconds == 60.0

    def test_raises_on_negative_default(self):
        with pytest.raises(ValueError):
            CooldownRegistry(default_cooldown_seconds=-1)

    def test_not_suppressed_before_any_record(self):
        assert not self.reg.is_suppressed("check_a")

    def test_suppressed_immediately_after_record(self):
        now = datetime.utcnow()
        self.reg.record("check_a", at=now)
        assert self.reg.is_suppressed("check_a", now=now)

    def test_not_suppressed_after_cooldown_expires(self):
        past = datetime.utcnow() - timedelta(seconds=120)
        self.reg.record("check_a", at=past)
        assert not self.reg.is_suppressed("check_a")

    def test_suppressed_within_cooldown_window(self):
        past = datetime.utcnow() - timedelta(seconds=30)
        self.reg.record("check_a", at=past)
        assert self.reg.is_suppressed("check_a")

    def test_reset_clears_record(self):
        self.reg.record("check_a")
        self.reg.reset("check_a")
        assert not self.reg.is_suppressed("check_a")

    def test_reset_all_clears_all(self):
        self.reg.record("check_a")
        self.reg.record("check_b")
        self.reg.reset_all()
        assert len(self.reg) == 0

    def test_len_reflects_recorded_checks(self):
        self.reg.record("check_a")
        self.reg.record("check_b")
        assert len(self.reg) == 2

    def test_override_cooldown_used(self):
        self.reg.set_override("check_a", 10.0)
        assert self.reg.cooldown_for("check_a") == 10.0

    def test_default_used_without_override(self):
        assert self.reg.cooldown_for("check_b") == 60.0

    def test_remove_override_restores_default(self):
        self.reg.set_override("check_a", 10.0)
        self.reg.remove_override("check_a")
        assert self.reg.cooldown_for("check_a") == 60.0

    def test_override_raises_on_negative(self):
        with pytest.raises(ValueError):
            self.reg.set_override("check_a", -5.0)

    def test_zero_cooldown_never_suppresses(self):
        reg = CooldownRegistry(default_cooldown_seconds=0)
        reg.record("check_a")
        assert not reg.is_suppressed("check_a")

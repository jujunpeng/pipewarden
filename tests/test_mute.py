"""Tests for pipewarden.mute (MuteRule and MuteRegistry)."""
from datetime import datetime, timedelta

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.mute import MuteRule, MuteRegistry


def _make_result(name: str = "check_a", status: CheckStatus = CheckStatus.FAILED) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="msg")


# ---------------------------------------------------------------------------
# MuteRule
# ---------------------------------------------------------------------------

class TestMuteRule:
    def test_repr_contains_name(self):
        rule = MuteRule(name="maintenance", condition=lambda r: True)
        assert "maintenance" in repr(rule)

    def test_is_active_with_no_expiry(self):
        rule = MuteRule(name="r", condition=lambda r: True)
        assert rule.is_active() is True

    def test_is_active_before_expiry(self):
        future = datetime.utcnow() + timedelta(hours=1)
        rule = MuteRule(name="r", condition=lambda r: True, expires_at=future)
        assert rule.is_active() is True

    def test_is_inactive_after_expiry(self):
        past = datetime.utcnow() - timedelta(seconds=1)
        rule = MuteRule(name="r", condition=lambda r: True, expires_at=past)
        assert rule.is_active() is False

    def test_matches_true_when_active_and_condition_true(self):
        rule = MuteRule(name="r", condition=lambda r: r.check_name == "check_a")
        result = _make_result("check_a")
        assert rule.matches(result) is True

    def test_matches_false_when_condition_false(self):
        rule = MuteRule(name="r", condition=lambda r: False)
        assert rule.matches(_make_result()) is False

    def test_matches_false_when_expired(self):
        past = datetime.utcnow() - timedelta(seconds=1)
        rule = MuteRule(name="r", condition=lambda r: True, expires_at=past)
        assert rule.matches(_make_result()) is False

    def test_matches_false_on_exception_in_condition(self):
        def bad(r):
            raise RuntimeError("boom")
        rule = MuteRule(name="r", condition=bad)
        assert rule.matches(_make_result()) is False


# ---------------------------------------------------------------------------
# MuteRegistry
# ---------------------------------------------------------------------------

class TestMuteRegistry:
    def setup_method(self):
        self.registry = MuteRegistry()

    def test_initial_rule_count_is_zero(self):
        assert self.registry.rule_count == 0

    def test_add_increments_count(self):
        self.registry.add(MuteRule("r", lambda r: True))
        assert self.registry.rule_count == 1

    def test_add_raises_on_non_rule(self):
        with pytest.raises(TypeError):
            self.registry.add("not-a-rule")  # type: ignore

    def test_is_muted_true_when_rule_matches(self):
        self.registry.add(MuteRule("r", lambda r: r.check_name == "check_a"))
        assert self.registry.is_muted(_make_result("check_a")) is True

    def test_is_muted_false_when_no_rule_matches(self):
        self.registry.add(MuteRule("r", lambda r: r.check_name == "other"))
        assert self.registry.is_muted(_make_result("check_a")) is False

    def test_remove_deletes_rule(self):
        self.registry.add(MuteRule("r", lambda r: True))
        self.registry.remove("r")
        assert self.registry.rule_count == 0

    def test_purge_expired_removes_expired_rules(self):
        past = datetime.utcnow() - timedelta(seconds=1)
        self.registry.add(MuteRule("expired", lambda r: True, expires_at=past))
        self.registry.add(MuteRule("active", lambda r: True))
        removed = self.registry.purge_expired()
        assert removed == 1
        assert self.registry.rule_count == 1

    def test_active_rules_excludes_expired(self):
        past = datetime.utcnow() - timedelta(seconds=1)
        self.registry.add(MuteRule("expired", lambda r: True, expires_at=past))
        self.registry.add(MuteRule("active", lambda r: True))
        assert len(self.registry.active_rules()) == 1

    def test_repr_contains_rule_count(self):
        assert "rules=0" in repr(self.registry)

"""Tests for pipewarden.registry."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewarden.checks import HealthCheck
from pipewarden.registry import CheckRegistry


def _make_check(name: str) -> HealthCheck:
    check = MagicMock(spec=HealthCheck)
    check.name = name
    return check


class TestCheckRegistry:
    def setup_method(self):
        self.registry = CheckRegistry()

    def test_register_and_get(self):
        check = _make_check("row-count")
        self.registry.register(check)
        assert self.registry.get("row-count") is check

    def test_register_duplicate_raises(self):
        check = _make_check("row-count")
        self.registry.register(check)
        with pytest.raises(ValueError, match="already registered"):
            self.registry.register(check)

    def test_unregister_removes_check(self):
        check = _make_check("row-count")
        self.registry.register(check)
        self.registry.unregister("row-count")
        assert "row-count" not in self.registry

    def test_unregister_missing_raises(self):
        with pytest.raises(KeyError):
            self.registry.unregister("nonexistent")

    def test_all_checks_returns_all(self):
        c1 = _make_check("c1")
        c2 = _make_check("c2")
        self.registry.register(c1)
        self.registry.register(c2)
        assert set(self.registry.all_checks()) == {c1, c2}

    def test_checks_by_tag_filters_correctly(self):
        c1 = _make_check("c1")
        c2 = _make_check("c2")
        c3 = _make_check("c3")
        self.registry.register(c1, tags=["sales"])
        self.registry.register(c2, tags=["sales", "finance"])
        self.registry.register(c3, tags=["finance"])
        result = self.registry.checks_by_tag("sales")
        assert c1 in result
        assert c2 in result
        assert c3 not in result

    def test_checks_by_tag_returns_empty_for_unknown_tag(self):
        assert self.registry.checks_by_tag("unknown") == []

    def test_tags_for_returns_correct_tags(self):
        check = _make_check("c1")
        self.registry.register(check, tags=["a", "b"])
        assert sorted(self.registry.tags_for("c1")) == ["a", "b"]

    def test_len_reflects_registered_count(self):
        assert len(self.registry) == 0
        self.registry.register(_make_check("c1"))
        assert len(self.registry) == 1
        self.registry.register(_make_check("c2"))
        assert len(self.registry) == 2

    def test_contains_operator(self):
        check = _make_check("c1")
        self.registry.register(check)
        assert "c1" in self.registry
        assert "c2" not in self.registry

    def test_register_without_tags_defaults_to_empty(self):
        check = _make_check("c1")
        self.registry.register(check)
        assert self.registry.tags_for("c1") == []

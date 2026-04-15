"""Tests for pipewarden.tagging.TagIndex."""

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.tagging import TagIndex


def _make_result(name: str, status: CheckStatus = CheckStatus.PASSED) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="ok")


class TestTagIndex:
    def setup_method(self):
        self.index = TagIndex()

    # ------------------------------------------------------------------
    # basic add / get
    # ------------------------------------------------------------------

    def test_empty_index_has_zero_len(self):
        assert len(self.index) == 0

    def test_add_increments_len(self):
        self.index.add(_make_result("a"), ["db"])
        assert len(self.index) == 1

    def test_get_by_tag_returns_matching(self):
        r = _make_result("a")
        self.index.add(r, ["db", "critical"])
        assert r in self.index.get_by_tag("db")
        assert r in self.index.get_by_tag("critical")

    def test_get_by_tag_unknown_returns_empty(self):
        assert self.index.get_by_tag("nonexistent") == []

    def test_get_by_tag_returns_copy(self):
        r = _make_result("a")
        self.index.add(r, ["x"])
        lst = self.index.get_by_tag("x")
        lst.clear()
        assert len(self.index.get_by_tag("x")) == 1

    # ------------------------------------------------------------------
    # get_by_tags — match_all (default)
    # ------------------------------------------------------------------

    def test_get_by_tags_match_all_intersection(self):
        r1 = _make_result("r1")
        r2 = _make_result("r2")
        self.index.add(r1, ["db", "critical"])
        self.index.add(r2, ["db"])
        result = self.index.get_by_tags(["db", "critical"])
        assert r1 in result
        assert r2 not in result

    def test_get_by_tags_match_any_union(self):
        r1 = _make_result("r1")
        r2 = _make_result("r2")
        self.index.add(r1, ["db"])
        self.index.add(r2, ["cache"])
        result = self.index.get_by_tags(["db", "cache"], match_all=False)
        assert r1 in result
        assert r2 in result

    def test_get_by_tags_empty_tags_returns_all(self):
        r1 = _make_result("r1")
        r2 = _make_result("r2")
        self.index.add(r1, ["a"])
        self.index.add(r2, ["b"])
        assert len(self.index.get_by_tags([])) == 2

    # ------------------------------------------------------------------
    # known_tags / group_by_tag
    # ------------------------------------------------------------------

    def test_known_tags_reflects_added_tags(self):
        self.index.add(_make_result("a"), ["db", "critical"])
        self.index.add(_make_result("b"), ["cache"])
        assert self.index.known_tags() == frozenset({"db", "critical", "cache"})

    def test_group_by_tag_keys_match_known_tags(self):
        self.index.add(_make_result("a"), ["db"])
        self.index.add(_make_result("b"), ["db", "cache"])
        grouped = self.index.group_by_tag()
        assert set(grouped.keys()) == {"db", "cache"}
        assert len(grouped["db"]) == 2

    # ------------------------------------------------------------------
    # failed_by_tag
    # ------------------------------------------------------------------

    def test_failed_by_tag_excludes_passed(self):
        r_pass = _make_result("ok", CheckStatus.PASSED)
        r_fail = _make_result("bad", CheckStatus.FAILED)
        self.index.add(r_pass, ["db"])
        self.index.add(r_fail, ["db"])
        failures = self.index.failed_by_tag("db")
        assert r_fail in failures
        assert r_pass not in failures

    def test_failed_by_tag_includes_error_status(self):
        r_err = _make_result("err", CheckStatus.ERROR)
        self.index.add(r_err, ["infra"])
        assert r_err in self.index.failed_by_tag("infra")

    def test_failed_by_tag_unknown_tag_returns_empty(self):
        assert self.index.failed_by_tag("ghost") == []

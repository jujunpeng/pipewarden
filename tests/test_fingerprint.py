"""Tests for pipewarden.fingerprint."""

from __future__ import annotations

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.fingerprint import FingerprintIndex, _fingerprint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(name: str = "check_a", status: CheckStatus = CheckStatus.PASSED) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="ok")


# ---------------------------------------------------------------------------
# _fingerprint function
# ---------------------------------------------------------------------------

class TestFingerprintFunction:
    def test_same_name_and_status_give_same_fingerprint(self):
        r1 = _make_result("check_a", CheckStatus.PASSED)
        r2 = _make_result("check_a", CheckStatus.PASSED)
        assert _fingerprint(r1) == _fingerprint(r2)

    def test_different_status_gives_different_fingerprint(self):
        r1 = _make_result("check_a", CheckStatus.PASSED)
        r2 = _make_result("check_a", CheckStatus.FAILED)
        assert _fingerprint(r1) != _fingerprint(r2)

    def test_different_name_gives_different_fingerprint(self):
        r1 = _make_result("check_a", CheckStatus.PASSED)
        r2 = _make_result("check_b", CheckStatus.PASSED)
        assert _fingerprint(r1) != _fingerprint(r2)

    def test_fingerprint_is_64_hex_chars(self):
        r = _make_result()
        fp = _fingerprint(r)
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)

    def test_timestamp_does_not_affect_fingerprint(self):
        """Two results recorded at different times must share a fingerprint."""
        import time
        r1 = _make_result()
        time.sleep(0.01)
        r2 = _make_result()
        assert _fingerprint(r1) == _fingerprint(r2)


# ---------------------------------------------------------------------------
# FingerprintIndex
# ---------------------------------------------------------------------------

class TestFingerprintIndex:
    def setup_method(self):
        self.index = FingerprintIndex()

    def test_initial_len_is_zero(self):
        assert len(self.index) == 0

    def test_add_returns_fingerprint_string(self):
        r = _make_result()
        fp = self.index.add(r)
        assert isinstance(fp, str) and len(fp) == 64

    def test_add_increments_len(self):
        self.index.add(_make_result("a", CheckStatus.PASSED))
        self.index.add(_make_result("b", CheckStatus.FAILED))
        assert len(self.index) == 2

    def test_two_results_same_fingerprint_both_stored(self):
        r1 = _make_result("check_a", CheckStatus.PASSED)
        r2 = _make_result("check_a", CheckStatus.PASSED)
        self.index.add(r1)
        self.index.add(r2)
        assert len(self.index) == 2

    def test_get_returns_matching_results(self):
        r = _make_result("check_a", CheckStatus.PASSED)
        fp = self.index.add(r)
        results = self.index.get(fp)
        assert r in results

    def test_get_unknown_fingerprint_returns_empty_list(self):
        assert self.index.get("nonexistent" * 4) == []

    def test_get_returns_copy(self):
        r = _make_result()
        fp = self.index.add(r)
        copy = self.index.get(fp)
        copy.append(_make_result("injected"))
        assert len(self.index.get(fp)) == 1

    def test_known_fingerprints_lists_all_unique_fps(self):
        self.index.add(_make_result("a", CheckStatus.PASSED))
        self.index.add(_make_result("b", CheckStatus.FAILED))
        self.index.add(_make_result("a", CheckStatus.PASSED))  # duplicate fp
        assert len(self.index.known_fingerprints) == 2

    def test_fingerprint_for_does_not_index(self):
        r = _make_result()
        _ = self.index.fingerprint_for(r)
        assert len(self.index) == 0

    def test_fingerprint_for_matches_add(self):
        r = _make_result()
        fp_add = self.index.add(r)
        fp_query = self.index.fingerprint_for(r)
        assert fp_add == fp_query

    def test_clear_removes_all_entries(self):
        self.index.add(_make_result("a"))
        self.index.add(_make_result("b"))
        self.index.clear()
        assert len(self.index) == 0
        assert self.index.known_fingerprints == []

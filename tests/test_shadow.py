"""Tests for pipewarden.shadow."""
from __future__ import annotations

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.shadow import ShadowDiff, ShadowRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(name: str, status: CheckStatus, duration_ms: float = 10.0) -> CheckResult:
    return CheckResult(check_name=name, status=status, duration_ms=duration_ms)


def _shadow_fn_passing(check_name: str) -> CheckResult:
    return _make_result(check_name, CheckStatus.PASSED)


def _shadow_fn_failing(check_name: str) -> CheckResult:
    return _make_result(check_name, CheckStatus.FAILED)


def _shadow_fn_raises(check_name: str) -> CheckResult:  # noqa: ARG001
    raise RuntimeError("shadow exploded")


# ---------------------------------------------------------------------------
# ShadowDiff
# ---------------------------------------------------------------------------

class TestShadowDiff:
    def test_diverged_when_statuses_differ(self):
        diff = ShadowDiff("c", CheckStatus.PASSED, CheckStatus.FAILED)
        assert diff.diverged is True

    def test_not_diverged_when_statuses_same(self):
        diff = ShadowDiff("c", CheckStatus.PASSED, CheckStatus.PASSED)
        assert diff.diverged is False

    def test_check_name_stored(self):
        diff = ShadowDiff("my_check", CheckStatus.FAILED, CheckStatus.PASSED)
        assert diff.check_name == "my_check"

    def test_live_status_stored(self):
        diff = ShadowDiff("c", CheckStatus.ERROR, CheckStatus.PASSED)
        assert diff.live_status == CheckStatus.ERROR

    def test_shadow_status_stored(self):
        diff = ShadowDiff("c", CheckStatus.PASSED, CheckStatus.ERROR)
        assert diff.shadow_status == CheckStatus.ERROR


# ---------------------------------------------------------------------------
# ShadowRunner
# ---------------------------------------------------------------------------

class TestShadowRunner:
    def setup_method(self):
        self.runner = ShadowRunner(_shadow_fn_passing)

    def test_raises_on_non_callable(self):
        with pytest.raises(TypeError):
            ShadowRunner("not_a_function")  # type: ignore[arg-type]

    def test_initial_divergence_count_is_zero(self):
        assert self.runner.divergence_count == 0

    def test_initial_diffs_empty(self):
        assert self.runner.diffs() == []

    def test_observe_returns_none_when_no_divergence(self):
        live = _make_result("check_a", CheckStatus.PASSED)
        result = self.runner.observe(live)
        assert result is None

    def test_observe_returns_diff_on_divergence(self):
        runner = ShadowRunner(_shadow_fn_failing)
        live = _make_result("check_a", CheckStatus.PASSED)
        diff = runner.observe(live)
        assert diff is not None
        assert diff.diverged is True
        assert diff.check_name == "check_a"

    def test_divergence_count_increments(self):
        runner = ShadowRunner(_shadow_fn_failing)
        live = _make_result("check_a", CheckStatus.PASSED)
        runner.observe(live)
        runner.observe(live)
        assert runner.divergence_count == 2

    def test_diffs_accumulate(self):
        runner = ShadowRunner(_shadow_fn_failing)
        live = _make_result("check_a", CheckStatus.PASSED)
        runner.observe(live)
        runner.observe(live)
        assert len(runner.diffs()) == 2

    def test_diffs_returns_copy(self):
        runner = ShadowRunner(_shadow_fn_failing)
        live = _make_result("check_a", CheckStatus.PASSED)
        runner.observe(live)
        copy1 = runner.diffs()
        copy1.clear()
        assert len(runner.diffs()) == 1

    def test_shadow_exception_does_not_propagate(self):
        runner = ShadowRunner(_shadow_fn_raises)
        live = _make_result("check_a", CheckStatus.PASSED)
        result = runner.observe(live)  # must not raise
        assert result is None

    def test_shadow_exception_does_not_increment_divergence(self):
        runner = ShadowRunner(_shadow_fn_raises)
        live = _make_result("check_a", CheckStatus.PASSED)
        runner.observe(live)
        assert runner.divergence_count == 0

    def test_reset_clears_diffs(self):
        runner = ShadowRunner(_shadow_fn_failing)
        live = _make_result("check_a", CheckStatus.PASSED)
        runner.observe(live)
        runner.reset()
        assert runner.diffs() == []

    def test_reset_clears_divergence_count(self):
        runner = ShadowRunner(_shadow_fn_failing)
        live = _make_result("check_a", CheckStatus.PASSED)
        runner.observe(live)
        runner.reset()
        assert runner.divergence_count == 0

    def test_no_divergence_not_stored_in_diffs(self):
        live = _make_result("check_a", CheckStatus.PASSED)
        self.runner.observe(live)
        assert self.runner.diffs() == []

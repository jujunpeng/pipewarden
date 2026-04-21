"""Tests for pipewarden.score."""

from __future__ import annotations

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.score import HealthScore, PipelineScorer, ScoringWeights


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status)


# ---------------------------------------------------------------------------
# ScoringWeights
# ---------------------------------------------------------------------------

class TestScoringWeights:
    def test_default_values(self):
        w = ScoringWeights()
        assert w.passed_weight == 1.0
        assert w.failed_weight == 0.0
        assert w.error_weight == 0.0

    def test_custom_values(self):
        w = ScoringWeights(passed_weight=1.0, failed_weight=0.5, error_weight=0.2)
        assert w.failed_weight == 0.5
        assert w.error_weight == 0.2

    def test_raises_on_weight_above_one(self):
        with pytest.raises(ValueError, match="passed_weight"):
            ScoringWeights(passed_weight=1.1)

    def test_raises_on_negative_weight(self):
        with pytest.raises(ValueError, match="failed_weight"):
            ScoringWeights(failed_weight=-0.1)


# ---------------------------------------------------------------------------
# HealthScore
# ---------------------------------------------------------------------------

class TestHealthScore:
    def test_grade_a_at_100(self):
        hs = HealthScore(score=100.0, total=5, breakdown={})
        assert hs.grade == "A"

    def test_grade_b_at_80(self):
        hs = HealthScore(score=80.0, total=5, breakdown={})
        assert hs.grade == "B"

    def test_grade_c_at_60(self):
        hs = HealthScore(score=60.0, total=5, breakdown={})
        assert hs.grade == "C"

    def test_grade_f_at_40(self):
        hs = HealthScore(score=40.0, total=5, breakdown={})
        assert hs.grade == "F"


# ---------------------------------------------------------------------------
# PipelineScorer
# ---------------------------------------------------------------------------

class TestPipelineScorer:
    def setup_method(self):
        self.scorer = PipelineScorer()

    def test_empty_results_returns_perfect_score(self):
        hs = self.scorer.score([])
        assert hs.score == 100.0
        assert hs.total == 0

    def test_all_passed_returns_100(self):
        results = [_make_result(f"c{i}", CheckStatus.PASSED) for i in range(5)]
        hs = self.scorer.score(results)
        assert hs.score == 100.0
        assert hs.total == 5

    def test_all_failed_returns_0(self):
        results = [_make_result(f"c{i}", CheckStatus.FAILED) for i in range(3)]
        hs = self.scorer.score(results)
        assert hs.score == 0.0

    def test_mixed_results_score(self):
        results = [
            _make_result("a", CheckStatus.PASSED),
            _make_result("b", CheckStatus.PASSED),
            _make_result("c", CheckStatus.FAILED),
            _make_result("d", CheckStatus.FAILED),
        ]
        hs = self.scorer.score(results)
        assert hs.score == 50.0

    def test_breakdown_counts_are_correct(self):
        results = [
            _make_result("a", CheckStatus.PASSED),
            _make_result("b", CheckStatus.FAILED),
            _make_result("c", CheckStatus.ERROR),
        ]
        hs = self.scorer.score(results)
        assert hs.breakdown[CheckStatus.PASSED.value] == 1
        assert hs.breakdown[CheckStatus.FAILED.value] == 1
        assert hs.breakdown[CheckStatus.ERROR.value] == 1

    def test_custom_weights_partial_credit_for_failures(self):
        weights = ScoringWeights(passed_weight=1.0, failed_weight=0.5, error_weight=0.0)
        scorer = PipelineScorer(weights=weights)
        results = [
            _make_result("a", CheckStatus.PASSED),
            _make_result("b", CheckStatus.FAILED),
        ]
        hs = scorer.score(results)
        # (1.0 + 0.5) / 2 * 100 = 75.0
        assert hs.score == 75.0

    def test_weights_property_returns_weights(self):
        w = ScoringWeights(failed_weight=0.3)
        scorer = PipelineScorer(weights=w)
        assert scorer.weights is w

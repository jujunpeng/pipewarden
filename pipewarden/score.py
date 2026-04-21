"""Pipeline health scoring module.

Computes a numeric health score (0.0–100.0) for a pipeline run based on
check results, weighting failures and errors differently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from pipewarden.checks import CheckResult, CheckStatus


@dataclass
class ScoringWeights:
    """Weights used when computing the health score."""

    passed_weight: float = 1.0
    failed_weight: float = 0.0
    error_weight: float = 0.0

    def __post_init__(self) -> None:
        for attr in ("passed_weight", "failed_weight", "error_weight"):
            val = getattr(self, attr)
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"{attr} must be between 0.0 and 1.0, got {val}"
                )


@dataclass
class HealthScore:
    """Result of scoring a collection of check results."""

    score: float
    total: int
    breakdown: Dict[str, int] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"HealthScore(score={self.score:.1f}, total={self.total}, "
            f"breakdown={self.breakdown})"
        )

    @property
    def grade(self) -> str:
        """Letter grade derived from the numeric score."""
        if self.score >= 90.0:
            return "A"
        if self.score >= 75.0:
            return "B"
        if self.score >= 50.0:
            return "C"
        return "F"


class PipelineScorer:
    """Computes a health score for a list of CheckResult objects."""

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        self._weights = weights or ScoringWeights()

    @property
    def weights(self) -> ScoringWeights:
        return self._weights

    def score(self, results: list[CheckResult]) -> HealthScore:
        """Return a HealthScore for *results*."""
        if not results:
            return HealthScore(score=100.0, total=0, breakdown={})

        w = self._weights
        weight_map = {
            CheckStatus.PASSED: w.passed_weight,
            CheckStatus.FAILED: w.failed_weight,
            CheckStatus.ERROR: w.error_weight,
        }

        breakdown: Dict[str, int] = {s.value: 0 for s in CheckStatus}
        weighted_sum = 0.0

        for result in results:
            breakdown[result.status.value] += 1
            weighted_sum += weight_map.get(result.status, 0.0)

        raw = (weighted_sum / len(results)) * 100.0
        return HealthScore(
            score=round(raw, 2),
            total=len(results),
            breakdown=breakdown,
        )
